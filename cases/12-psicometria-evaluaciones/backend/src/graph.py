"""
graph.py — Grafo LangGraph para el Caso 12: Psicometría y Evaluaciones.

Pipeline de validación psicométrica de un instrumento:

  cargar_especificacion → revisar_items → ensamblar_instrumento
       → aplicar_evaluacion → analisis_psicometrico → {router validez}
              ├─ valido           → calibrar_baremos
              └─ requiere_revision (iter < tope) → revisar_items_problematicos
                                                       ↓
                                              analisis_psicometrico (loop)
       calibrar_baremos → generar_informe_individual
                              → generar_informe_grupal → END

10 nodos · 1 router (validez) · 1 loop con tope (max_iteraciones_validez).

Helpers deterministas:
  - alpha de Cronbach
  - índice de dificultad (p para dicotómico, media para Likert)
  - índice de discriminación (rpb / item-total corregido)
  - DIF entre grupos (diferencia |p_grupo_a − p_grupo_b|)

LIVE opt-in con OPENAI_API_KEY para reporte ejecutivo enriquecido.
"""
from __future__ import annotations

import logging
import math
import operator
import os
import statistics
from datetime import datetime
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import (
    generate_responses,
    get_instrument,
    get_item_bank,
    get_policy,
)
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class EvalState(TypedDict):
    instrument_id: str
    instrument: dict
    policy: dict
    items_candidatos: list
    items_revisados: list
    items_rechazados_revision: list
    items_aprobados: list
    respuestas: list
    instrumento_actual: list
    psicometria: dict
    items_problematicos: list
    iteracion_validez: int
    valido: bool
    baremos: dict
    puntajes_individuales: list
    informe_grupal: dict
    reporte: str
    events: Annotated[list, operator.add]
    done: bool


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

def _llm_invoke(prompt: str, fallback: str) -> str:
    if not _LIVE_MODE:
        return fallback
    try:
        from langchain_openai import ChatOpenAI  # noqa: PLC0415
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model_name, temperature=0)
        return llm.invoke(prompt).content
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM no disponible, fallback DEMO: %s", exc)
        return fallback


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Helpers psicométricos (deterministas, sin dependencias externas)
# ---------------------------------------------------------------------------

def alpha_cronbach(matrix: list[list[float]]) -> float:
    """
    matrix: lista de filas; cada fila = respuestas de un evaluado a los k ítems.
    Devuelve α de Cronbach. 0 si no hay datos suficientes.
    """
    if not matrix or len(matrix) < 2:
        return 0.0
    k = len(matrix[0])
    if k < 2:
        return 0.0
    # var por ítem (columnas)
    var_items = []
    for j in range(k):
        col = [float(row[j]) for row in matrix]
        try:
            var_items.append(statistics.variance(col))
        except statistics.StatisticsError:
            var_items.append(0.0)
    totales = [sum(row) for row in matrix]
    try:
        var_total = statistics.variance(totales)
    except statistics.StatisticsError:
        var_total = 0.0
    if var_total <= 0:
        return 0.0
    return (k / (k - 1)) * (1.0 - sum(var_items) / var_total)


def indice_dificultad(item_responses: list[float], formato: str) -> float:
    """Dicotómico: proporción de aciertos. Likert: media (1-5)."""
    if not item_responses:
        return 0.0
    if formato == "likert":
        return round(statistics.mean(item_responses), 3)
    return round(sum(1 for x in item_responses if x >= 0.5) / len(item_responses), 3)


def indice_discriminacion(item_responses: list[float], total_scores: list[float]) -> float:
    """
    Item-total corregido (correlación de Pearson). Mide cuánto separa el ítem
    a evaluados altos vs bajos en el total.
    """
    if len(item_responses) < 3 or len(item_responses) != len(total_scores):
        return 0.0
    # total corregido = total - este ítem
    corrected = [t - r for t, r in zip(total_scores, item_responses)]
    try:
        mean_i = statistics.mean(item_responses)
        mean_c = statistics.mean(corrected)
        cov = sum((a - mean_i) * (b - mean_c) for a, b in zip(item_responses, corrected)) / len(item_responses)
        var_i = statistics.pvariance(item_responses)
        var_c = statistics.pvariance(corrected)
        if var_i <= 0 or var_c <= 0:
            return 0.0
        return round(cov / math.sqrt(var_i * var_c), 3)
    except (statistics.StatisticsError, ValueError, ZeroDivisionError):
        return 0.0


def dif_entre_grupos(
    item_responses_por_evaluado: list[dict],
    item_id: str,
    grupos: list[str],
    formato: str,
) -> float:
    """
    DIF: diferencia absoluta entre el índice de dificultad de cada grupo.
    Si hay solo un grupo, devuelve 0.
    """
    if len(grupos) < 2:
        return 0.0
    indices: list[float] = []
    for g in grupos:
        vals = [
            float(r["respuestas"].get(item_id, 0))
            for r in item_responses_por_evaluado
            if r.get("grupo") == g and item_id in r.get("respuestas", {})
        ]
        if not vals:
            continue
        indices.append(indice_dificultad(vals, formato))
    if len(indices) < 2:
        return 0.0
    return round(max(indices) - min(indices), 3)


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def cargar_especificacion(state: EvalState) -> dict:
    """Carga instrumento, banco de ítems candidatos, política y cohorte piloto."""
    inst_id = state.get("instrument_id", "INST-COMP-DIG-01")
    data = get_data_dir()
    instrument = get_instrument(inst_id, data)
    items = get_item_bank(inst_id, data)
    policy = get_policy(data)

    logger.info(
        "Especificación cargada: instrumento=%s items_candidatos=%d formato=%s",
        inst_id, len(items), instrument.get("formato"),
    )

    return {
        "instrument": instrument,
        "policy": policy,
        "items_candidatos": items,
        "items_revisados": [],
        "items_rechazados_revision": [],
        "items_aprobados": [],
        "respuestas": [],
        "instrumento_actual": [],
        "psicometria": {},
        "items_problematicos": [],
        "iteracion_validez": 0,
        "valido": False,
        "baremos": {},
        "puntajes_individuales": [],
        "informe_grupal": {},
        "reporte": "",
        "done": False,
        "events": [{
            "type": "especificacion_cargada",
            "instrument_id": inst_id,
            "nombre": instrument.get("nombre"),
            "constructo": instrument.get("constructo"),
            "formato": instrument.get("formato"),
            "items_candidatos": len(items),
            "n_objetivo": instrument.get("n_items_objetivo"),
        }],
    }


def revisar_items(state: EvalState) -> dict:
    """
    Revisión experta determinista: marca ítems con claridad/representatividad
    bajas o sesgo estimado alto como rechazados antes del pilotaje.
    """
    policy = state.get("policy", {})
    instrument = state.get("instrument", {})
    candidatos = state.get("items_candidatos", [])

    umbral_claridad = float(policy.get("umbral_claridad_min", 0.70))
    umbral_repr = float(policy.get("umbral_representatividad_min", 0.70))
    umbral_sesgo = float(policy.get("umbral_sesgo_max", 0.15))

    revisados: list = []
    rechazados: list = []
    aprobados: list = []
    for it in candidatos:
        claridad = float(it.get("claridad", 0.85))
        repr_ = float(it.get("representatividad", 0.85))
        sesgo = float(it.get("sesgo_estimado", 0.0))
        razones = []
        if claridad < umbral_claridad:
            razones.append(f"claridad<{umbral_claridad}")
        if repr_ < umbral_repr:
            razones.append(f"representatividad<{umbral_repr}")
        if sesgo > umbral_sesgo:
            razones.append(f"sesgo>{umbral_sesgo}")
        flag = {"id": it["id"], "razones": razones, "aprobado": len(razones) == 0}
        revisados.append(flag)
        if razones:
            rechazados.append(it["id"])
        else:
            aprobados.append(it)

    logger.info(
        "Revisión expertos: %d aprobados / %d rechazados (instrumento=%s)",
        len(aprobados), len(rechazados), instrument.get("id"),
    )

    return {
        "items_revisados": revisados,
        "items_rechazados_revision": rechazados,
        "items_aprobados": aprobados,
        "events": [{
            "type": "items_revisados",
            "aprobados": len(aprobados),
            "rechazados": len(rechazados),
            "ids_rechazados": rechazados,
        }],
    }


def ensamblar_instrumento(state: EvalState) -> dict:
    """Selecciona hasta n_items_objetivo respetando representatividad por concepto."""
    instrument = state.get("instrument", {})
    aprobados = state.get("items_aprobados", [])
    n_obj = int(instrument.get("n_items_objetivo", len(aprobados)))

    # Balancea por concepto: orden estable por concepto, luego corte
    by_concepto: dict[str, list] = {}
    for it in aprobados:
        by_concepto.setdefault(it.get("concepto", "general"), []).append(it)

    seleccion: list = []
    while len(seleccion) < n_obj and any(by_concepto.values()):
        for cpt, lst in list(by_concepto.items()):
            if not lst:
                continue
            seleccion.append(lst.pop(0))
            if len(seleccion) >= n_obj:
                break

    logger.info(
        "Instrumento ensamblado: %d ítems (objetivo=%d)",
        len(seleccion), n_obj,
    )

    return {
        "instrumento_actual": seleccion,
        "events": [{
            "type": "instrumento_ensamblado",
            "n_items": len(seleccion),
            "ids": [it["id"] for it in seleccion],
            "conceptos": sorted({it.get("concepto", "general") for it in seleccion}),
        }],
    }


def aplicar_evaluacion(state: EvalState) -> dict:
    """Simula el pilotaje: genera la matriz de respuestas de la cohorte."""
    instrument = state.get("instrument", {})
    instrumento_actual = state.get("instrumento_actual", [])
    respuestas = generate_responses(instrument, instrumento_actual)

    logger.info(
        "Pilotaje aplicado: %d evaluados × %d ítems",
        len(respuestas), len(instrumento_actual),
    )

    return {
        "respuestas": respuestas,
        "events": [{
            "type": "pilotaje_aplicado",
            "n_evaluados": len(respuestas),
            "n_items": len(instrumento_actual),
            "grupos": sorted({r.get("grupo") for r in respuestas if r.get("grupo")}),
        }],
    }


def analisis_psicometrico(state: EvalState) -> dict:
    """Calcula α, dificultad p, discriminación rpb y DIF por ítem."""
    instrument = state.get("instrument", {})
    items = state.get("instrumento_actual", [])
    respuestas = state.get("respuestas", [])
    formato = instrument.get("formato", "dicotomico")
    grupos = instrument.get("grupos_dif", []) or []
    excluidos = set(state.get("items_problematicos", []))

    activos = [it for it in items if it["id"] not in excluidos]
    matrix = [
        [float(r["respuestas"].get(it["id"], 0)) for it in activos]
        for r in respuestas
    ]
    totales = [sum(row) for row in matrix]
    alpha = round(alpha_cronbach(matrix), 3) if matrix else 0.0

    item_metrics = []
    for j, it in enumerate(activos):
        col = [row[j] for row in matrix]
        p = indice_dificultad(col, formato)
        d = indice_discriminacion(col, totales)
        dif = dif_entre_grupos(respuestas, it["id"], grupos, formato)
        item_metrics.append({
            "id": it["id"],
            "concepto": it.get("concepto"),
            "dificultad": p,
            "discriminacion": d,
            "dif_entre_grupos": dif,
        })

    iteracion = int(state.get("iteracion_validez", 0)) + 1
    logger.info(
        "Análisis psicométrico (iter %d): α=%.3f items_activos=%d",
        iteracion, alpha, len(activos),
    )

    return {
        "psicometria": {
            "alpha_cronbach": alpha,
            "n_items_activos": len(activos),
            "n_evaluados": len(respuestas),
            "totales": totales,
            "items": item_metrics,
            "formato": formato,
        },
        "iteracion_validez": iteracion,
        "events": [{
            "type": "psicometria_calculada",
            "iteracion": iteracion,
            "alpha": alpha,
            "n_items_activos": len(activos),
        }],
    }


# ---------------------------------------------------------------------------
# Router de validez (con loop tope)
# ---------------------------------------------------------------------------

def validez_router(state: EvalState) -> str:
    instrument = state.get("instrument", {})
    psicometria = state.get("psicometria", {})
    policy = state.get("policy", {})

    umbral_alpha = float(instrument.get("umbral_alpha", 0.70))
    alpha = float(psicometria.get("alpha_cronbach", 0.0))
    max_iter = int(policy.get("max_iteraciones_validez", 2))
    iter_actual = int(state.get("iteracion_validez", 0))

    if alpha >= umbral_alpha:
        return "valido"
    if iter_actual >= max_iter:
        return "valido"  # tope alcanzado → continuar para no bloquear el caso
    return "requiere_revision"


def revisar_items_problematicos(state: EvalState) -> dict:
    """
    Excluye ítems con dificultad fuera de rango, discriminación baja
    o DIF alto. Re-ejecuta el análisis con el subconjunto restante.
    """
    instrument = state.get("instrument", {})
    psicometria = state.get("psicometria", {})

    dif_min = float(instrument.get("umbral_dificultad_min", 0.20))
    dif_max = float(instrument.get("umbral_dificultad_max", 0.85))
    disc_min = float(instrument.get("umbral_discriminacion", 0.20))
    dif_max_grupos = float(instrument.get("umbral_dif", 0.20))

    problematicos = list(state.get("items_problematicos", []))
    razones_por_item: dict[str, list] = {}
    for m in psicometria.get("items", []):
        razones = []
        if m["dificultad"] < dif_min or m["dificultad"] > dif_max:
            razones.append(f"dificultad={m['dificultad']}")
        if abs(m["discriminacion"]) < disc_min:
            razones.append(f"discriminacion={m['discriminacion']}")
        if m["dif_entre_grupos"] > dif_max_grupos:
            razones.append(f"dif_grupos={m['dif_entre_grupos']}")
        if razones and m["id"] not in problematicos:
            problematicos.append(m["id"])
            razones_por_item[m["id"]] = razones

    logger.info(
        "Ítems problemáticos detectados: %s",
        list(razones_por_item.keys()),
    )

    return {
        "items_problematicos": problematicos,
        "events": [{
            "type": "items_problematicos_revisados",
            "nuevos": list(razones_por_item.keys()),
            "total_excluidos": len(problematicos),
            "razones": razones_por_item,
        }],
    }


# ---------------------------------------------------------------------------
# Calibración + reportes
# ---------------------------------------------------------------------------

def _percentil(score: float, sorted_scores: list[float]) -> int:
    if not sorted_scores:
        return 0
    n = len(sorted_scores)
    # rank = cantidad de puntajes <= score, ajustando empates al promedio
    cnt_below = sum(1 for s in sorted_scores if s < score)
    cnt_eq = sum(1 for s in sorted_scores if s == score)
    rank = cnt_below + 0.5 * cnt_eq
    return max(0, min(100, int(round(100 * rank / n))))


def _banda_para_percentil(perc: int, bandas: dict, etiquetas: dict) -> tuple[str, str]:
    if perc <= int(bandas.get("bajo", 25)):
        clave = "bajo"
    elif perc <= int(bandas.get("medio_bajo", 50)):
        clave = "medio_bajo"
    elif perc <= int(bandas.get("medio_alto", 75)):
        clave = "medio_alto"
    else:
        clave = "alto"
    return clave, etiquetas.get(clave, clave)


def calibrar_baremos(state: EvalState) -> dict:
    """Marca el instrumento como válido y calcula baremos por percentiles."""
    psicometria = state.get("psicometria", {})
    totales = list(psicometria.get("totales", []))
    if not totales:
        return {
            "valido": False,
            "baremos": {},
            "events": [{"type": "baremos_omitidos", "razon": "sin totales"}],
        }
    sorted_totales = sorted(totales)
    baremos = {
        "n": len(sorted_totales),
        "min": round(min(sorted_totales), 3),
        "max": round(max(sorted_totales), 3),
        "media": round(statistics.mean(sorted_totales), 3),
        "mediana": round(statistics.median(sorted_totales), 3),
        "p25": round(sorted_totales[int(0.25 * (len(sorted_totales) - 1))], 3),
        "p50": round(sorted_totales[int(0.50 * (len(sorted_totales) - 1))], 3),
        "p75": round(sorted_totales[int(0.75 * (len(sorted_totales) - 1))], 3),
    }
    logger.info("Baremos calibrados: %s", baremos)
    return {
        "valido": True,
        "baremos": baremos,
        "events": [{
            "type": "baremos_calibrados",
            "media": baremos["media"],
            "p25": baremos["p25"],
            "p75": baremos["p75"],
        }],
    }


def generar_informe_individual(state: EvalState) -> dict:
    """Genera puntaje, percentil, banda e interpretación por evaluado."""
    psicometria = state.get("psicometria", {})
    baremos = state.get("baremos", {})
    respuestas = state.get("respuestas", [])
    policy = state.get("policy", {})
    bandas = policy.get("bandas_percentiles", {})
    etiquetas = policy.get("etiquetas_bandas", {})
    totales = psicometria.get("totales", []) or []
    sorted_totales = sorted(totales)

    individuales = []
    for r, total in zip(respuestas, totales):
        perc = _percentil(total, sorted_totales)
        clave, etiqueta = _banda_para_percentil(perc, bandas, etiquetas)
        individuales.append({
            "evaluado_id": r.get("evaluado_id"),
            "grupo": r.get("grupo"),
            "puntaje_bruto": round(total, 3),
            "percentil": perc,
            "banda": clave,
            "interpretacion": etiqueta,
        })

    logger.info("Informes individuales: %d evaluados", len(individuales))
    return {
        "puntajes_individuales": individuales,
        "events": [{
            "type": "informes_individuales_generados",
            "n": len(individuales),
            "media_puntaje": baremos.get("media"),
        }],
    }


def generar_informe_grupal(state: EvalState) -> dict:
    """
    Informe grupal y reporte ejecutivo. LIVE opt-in con LLM para
    redacción enriquecida; fallback DEMO determinista.
    """
    instrument = state.get("instrument", {})
    psicometria = state.get("psicometria", {})
    baremos = state.get("baremos", {})
    individuales = state.get("puntajes_individuales", [])
    items_excluidos = state.get("items_problematicos", [])
    rechazados_revision = state.get("items_rechazados_revision", [])
    grupos = instrument.get("grupos_dif", []) or []

    # Distribución por banda
    dist_bandas: dict[str, int] = {"alto": 0, "medio_alto": 0, "medio_bajo": 0, "bajo": 0}
    for ind in individuales:
        dist_bandas[ind["banda"]] = dist_bandas.get(ind["banda"], 0) + 1

    # Medias por grupo
    medias_grupo: dict[str, float] = {}
    for g in grupos:
        vals = [ind["puntaje_bruto"] for ind in individuales if ind["grupo"] == g]
        if vals:
            medias_grupo[g] = round(statistics.mean(vals), 3)

    alpha = psicometria.get("alpha_cronbach", 0.0)
    umbral_alpha = instrument.get("umbral_alpha", 0.70)
    fiabilidad_ok = alpha >= umbral_alpha

    informe_grupal = {
        "alpha_cronbach": alpha,
        "umbral_alpha": umbral_alpha,
        "fiabilidad_aceptable": fiabilidad_ok,
        "n_items_activos": psicometria.get("n_items_activos", 0),
        "n_items_excluidos": len(items_excluidos) + len(rechazados_revision),
        "items_excluidos_revision": rechazados_revision,
        "items_excluidos_psicometria": items_excluidos,
        "distribucion_bandas": dist_bandas,
        "medias_por_grupo": medias_grupo,
        "baremos": baremos,
    }

    estado_icon = "🟢" if fiabilidad_ok else "🟡"
    fallback = (
        f"## Informe psicométrico — {instrument.get('nombre', '')}"
        f" ({instrument.get('id', '')})\n\n"
        f"**Constructo:** {instrument.get('constructo', '—')}\n"
        f"**Uso:** {instrument.get('uso', '—')}\n"
        f"**Formato:** {instrument.get('formato', '—')} · "
        f"**Cohorte:** {len(individuales)} evaluados\n\n"
        f"### Confiabilidad {estado_icon}\n"
        f"- α de Cronbach: **{alpha}** (umbral ≥ {umbral_alpha}) — "
        f"{'aceptable' if fiabilidad_ok else 'bajo umbral, requiere revisión'}\n"
        f"- Ítems activos: **{psicometria.get('n_items_activos', 0)}**\n"
        f"- Ítems excluidos en revisión: {len(rechazados_revision)} → {rechazados_revision or '—'}\n"
        f"- Ítems excluidos por psicometría: {len(items_excluidos)} → {items_excluidos or '—'}\n\n"
        f"### Distribución por banda\n"
        f"- Alto: {dist_bandas['alto']} · "
        f"Medio-alto: {dist_bandas['medio_alto']} · "
        f"Medio-bajo: {dist_bandas['medio_bajo']} · "
        f"Bajo: {dist_bandas['bajo']}\n\n"
        f"### Medias por grupo\n"
        + (
            "".join(f"- {g}: {m}\n" for g, m in medias_grupo.items())
            if medias_grupo else "- (sin desglose grupal)\n"
        )
        + f"\n### Baremos\n"
        f"- Media: {baremos.get('media', '—')} · "
        f"Mediana: {baremos.get('mediana', '—')} · "
        f"P25: {baremos.get('p25', '—')} · "
        f"P75: {baremos.get('p75', '—')}\n\n"
        f"_Informe generado por el agente psicométrico — Caso 12. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres un psicómetra que redacta un informe ejecutivo en español "
            f"(máx 220 palabras) para el comité técnico. "
            f"Instrumento: {instrument.get('nombre')} ({instrument.get('id')}). "
            f"Constructo: {instrument.get('constructo')}. "
            f"α de Cronbach: {alpha} (umbral {umbral_alpha}). "
            f"Ítems activos: {psicometria.get('n_items_activos')}. "
            f"Ítems excluidos (revisión): {rechazados_revision}. "
            f"Ítems excluidos (psicometría): {items_excluidos}. "
            f"Medias por grupo: {medias_grupo}. "
            f"Cierra con 2 acciones concretas para la próxima versión del instrumento."
        )
        reporte = _llm_invoke(prompt, fallback)
    else:
        reporte = fallback

    logger.info(
        "Informe grupal generado: instrumento=%s fiabilidad=%s modo=%s",
        instrument.get("id"), fiabilidad_ok, "LIVE" if _LIVE_MODE else "DEMO",
    )

    return {
        "informe_grupal": informe_grupal,
        "reporte": reporte,
        "done": True,
        "events": [{
            "type": "informe_grupal_generado",
            "instrument_id": instrument.get("id"),
            "alpha": alpha,
            "fiabilidad_aceptable": fiabilidad_ok,
            "n_evaluados": len(individuales),
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(EvalState)

    builder.add_node("cargar_especificacion", cargar_especificacion)
    builder.add_node("revisar_items", revisar_items)
    builder.add_node("ensamblar_instrumento", ensamblar_instrumento)
    builder.add_node("aplicar_evaluacion", aplicar_evaluacion)
    builder.add_node("analisis_psicometrico", analisis_psicometrico)
    builder.add_node("revisar_items_problematicos", revisar_items_problematicos)
    builder.add_node("calibrar_baremos", calibrar_baremos)
    builder.add_node("generar_informe_individual", generar_informe_individual)
    builder.add_node("generar_informe_grupal", generar_informe_grupal)

    builder.set_entry_point("cargar_especificacion")
    builder.add_edge("cargar_especificacion", "revisar_items")
    builder.add_edge("revisar_items", "ensamblar_instrumento")
    builder.add_edge("ensamblar_instrumento", "aplicar_evaluacion")
    builder.add_edge("aplicar_evaluacion", "analisis_psicometrico")

    builder.add_conditional_edges(
        "analisis_psicometrico",
        validez_router,
        {
            "valido": "calibrar_baremos",
            "requiere_revision": "revisar_items_problematicos",
        },
    )
    builder.add_edge("revisar_items_problematicos", "analisis_psicometrico")

    builder.add_edge("calibrar_baremos", "generar_informe_individual")
    builder.add_edge("generar_informe_individual", "generar_informe_grupal")
    builder.add_edge("generar_informe_grupal", END)

    return builder.compile(checkpointer=MemorySaver())
