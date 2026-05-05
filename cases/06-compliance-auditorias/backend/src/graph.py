"""
graph.py — Grafo LangGraph para el Caso 06: Compliance & Auditorías.

Pipeline de preparación de auditoría con trazabilidad inmutable:

  parsear_alcance → mapear_controles → recopilar_evidencias → verificar_completitud
       │                                                          │
       │                                          ┌───────────────┴─────────────────┐
       │                                          │ router severidad faltantes      │
       │                                          ▼                                 ▼
       │                                 escalar_responsable                validar_evidencias
       │                                          │                                 │
       │                                          └────────────┬────────────────────┘
       │                                                       ▼
       │                                              generar_expediente → log_trazabilidad
       │                                                                          │
       │                                                                          ▼
       └─────────────────────────────────────────────────────────────────► producir_resumen → END

Cada acción del agente queda registrada con hash SHA-256 encadenado
(cadena de custodia tipo append-only). LIVE opt-in con OPENAI_API_KEY
para narrativa ejecutiva del resumen.
"""
from __future__ import annotations

import hashlib
import json
import logging
import operator
import os
from datetime import datetime
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import get_escenario, get_marcos, get_validation_rules
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class ComplianceState(TypedDict):
    audit_id: str
    marco: str
    marco_nombre: str
    periodo: str
    descripcion_escenario: str
    controles_en_scope: list
    mapeo_controles: list
    evidencias: list
    cobertura: dict
    faltantes: list
    severidad_faltantes: str
    validaciones: list
    invalidas: list
    escalaciones: list
    expediente: dict
    trazabilidad: list
    score_cumplimiento: int
    metricas: dict
    riesgo: str
    resumen: str
    events: Annotated[list, operator.add]
    done: bool


# ---------------------------------------------------------------------------
# Helpers
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


def _parse_date(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        return None


def _periodo_bounds(periodo: str) -> tuple[datetime | None, datetime | None]:
    """Acepta formatos '2026-Q1', '2026-03', '2026'."""
    p = (periodo or "").strip()
    try:
        if "Q" in p:
            year, q = p.split("-Q")
            year_i = int(year); q_i = int(q)
            start_month = (q_i - 1) * 3 + 1
            end_month = start_month + 2
            start = datetime(year_i, start_month, 1)
            if end_month == 12:
                end = datetime(year_i, 12, 31)
            else:
                end = datetime(year_i, end_month + 1, 1)
            return start, end
        if "-" in p:
            year, month = p.split("-")
            year_i = int(year); month_i = int(month)
            start = datetime(year_i, month_i, 1)
            if month_i == 12:
                end = datetime(year_i, 12, 31)
            else:
                end = datetime(year_i, month_i + 1, 1)
            return start, end
        if p:
            year_i = int(p)
            return datetime(year_i, 1, 1), datetime(year_i, 12, 31)
    except Exception:
        return None, None
    return None, None


def _hash_entry(prev_hash: str, payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    h = hashlib.sha256()
    h.update(prev_hash.encode("utf-8"))
    h.update(canonical.encode("utf-8"))
    return h.hexdigest()


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _append_traza(trazabilidad: list, accion: str, detalle: dict) -> list:
    prev_hash = trazabilidad[-1]["hash"] if trazabilidad else "GENESIS"
    entry = {
        "seq": len(trazabilidad) + 1,
        "ts": _now_iso(),
        "accion": accion,
        "detalle": detalle,
        "prev_hash": prev_hash,
    }
    entry["hash"] = _hash_entry(prev_hash, {"seq": entry["seq"], "accion": accion, "detalle": detalle})
    return trazabilidad + [entry]


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def parsear_alcance(state: ComplianceState) -> dict:
    audit_id = state.get("audit_id", "AUD-001")
    sc = get_escenario(audit_id, get_data_dir())
    marcos = get_marcos(get_data_dir())
    marco_id = sc.get("marco", "")
    marco_info = marcos.get(marco_id, {})
    marco_nombre = marco_info.get("nombre", marco_id or "Sin marco")

    controles_en_scope = sc.get("controles_en_scope", [])

    traza = _append_traza([], "parsear_alcance", {
        "audit_id": audit_id,
        "marco": marco_id,
        "periodo": sc.get("periodo"),
        "controles_en_scope": controles_en_scope,
    })

    logger.info(
        "Alcance parseado: audit=%s marco=%s periodo=%s controles=%d",
        audit_id, marco_id, sc.get("periodo"), len(controles_en_scope),
    )

    return {
        "marco": marco_id,
        "marco_nombre": marco_nombre,
        "periodo": sc.get("periodo", ""),
        "descripcion_escenario": sc.get("descripcion", ""),
        "controles_en_scope": controles_en_scope,
        "evidencias": sc.get("evidencias", []),
        "trazabilidad": traza,
        "events": [{
            "type": "alcance_parseado",
            "audit_id": audit_id,
            "marco": marco_id,
            "periodo": sc.get("periodo"),
            "total_controles": len(controles_en_scope),
        }],
    }


def mapear_controles(state: ComplianceState) -> dict:
    marcos = get_marcos(get_data_dir())
    marco_id = state.get("marco", "")
    marco = marcos.get(marco_id, {})
    catalogo = marco.get("controles", {})

    mapeo = []
    for control_id in state.get("controles_en_scope", []):
        info = catalogo.get(control_id, {})
        mapeo.append({
            "control_id": control_id,
            "titulo": info.get("titulo", "(sin título)"),
            "fuente": info.get("fuente", "desconocida"),
            "owner": info.get("owner", "compliance@empresa.cl"),
            "criticidad": info.get("criticidad", "media"),
            "evidencia_requerida": info.get("evidencia_requerida", []),
        })

    fuentes = sorted({m["fuente"] for m in mapeo})
    owners = sorted({m["owner"] for m in mapeo})

    traza = _append_traza(state.get("trazabilidad", []), "mapear_controles", {
        "total_mapeados": len(mapeo),
        "fuentes": fuentes,
        "owners": owners,
    })

    logger.info(
        "Controles mapeados: %d controles, fuentes=%s owners=%s",
        len(mapeo), fuentes, owners,
    )

    return {
        "mapeo_controles": mapeo,
        "trazabilidad": traza,
        "events": [{
            "type": "controles_mapeados",
            "total_mapeados": len(mapeo),
            "fuentes": fuentes,
            "owners_unicos": len(owners),
        }],
    }


def recopilar_evidencias(state: ComplianceState) -> dict:
    """
    Construye un índice control→evidencias y calcula cobertura por
    evidencia requerida. Identifica los faltantes (control + tipo requerido
    sin evidencia recibida).
    """
    evidencias = state.get("evidencias", [])
    mapeo = state.get("mapeo_controles", [])

    indice: dict = {}
    for ev in evidencias:
        indice.setdefault(ev["control"], []).append(ev)

    cobertura = {}
    faltantes = []
    for ctl in mapeo:
        ctl_id = ctl["control_id"]
        recibidas = indice.get(ctl_id, [])
        tipos_recibidos = {e.get("tipo") for e in recibidas}
        requeridas = ctl.get("evidencia_requerida", [])
        faltan = [t for t in requeridas if t not in tipos_recibidos]
        cobertura[ctl_id] = {
            "requeridas": len(requeridas),
            "recibidas": len([t for t in requeridas if t in tipos_recibidos]),
            "extra": max(0, len(recibidas) - len(requeridas)),
        }
        for tipo in faltan:
            faltantes.append({
                "control_id": ctl_id,
                "titulo": ctl.get("titulo", ""),
                "tipo_evidencia": tipo,
                "owner": ctl.get("owner", ""),
                "criticidad": ctl.get("criticidad", "media"),
                "fuente": ctl.get("fuente", ""),
            })

    altas = sum(1 for f in faltantes if f["criticidad"] == "alta")
    severidad = "alta" if altas > 0 else ("media" if faltantes else "baja")

    traza = _append_traza(state.get("trazabilidad", []), "recopilar_evidencias", {
        "total_evidencias": len(evidencias),
        "controles_con_evidencia": len(indice),
        "faltantes": len(faltantes),
        "faltantes_alta_criticidad": altas,
    })

    logger.info(
        "Evidencias recopiladas: total=%d, faltantes=%d (alta=%d), severidad=%s",
        len(evidencias), len(faltantes), altas, severidad,
    )

    return {
        "cobertura": cobertura,
        "faltantes": faltantes,
        "severidad_faltantes": severidad,
        "trazabilidad": traza,
        "events": [{
            "type": "evidencias_recopiladas",
            "total_evidencias": len(evidencias),
            "faltantes": len(faltantes),
            "faltantes_alta": altas,
            "severidad": severidad,
        }],
    }


def verificar_completitud(state: ComplianceState) -> Literal["escalar_responsable", "validar_evidencias"]:
    """Router: si hay faltantes de alta criticidad → escalar; si no → validar."""
    return "escalar_responsable" if state.get("severidad_faltantes") == "alta" else "validar_evidencias"


def escalar_responsable(state: ComplianceState) -> dict:
    """Genera notificaciones a los owners por cada faltante de alta criticidad."""
    faltantes = [f for f in state.get("faltantes", []) if f["criticidad"] == "alta"]
    audit_id = state.get("audit_id", "")
    periodo = state.get("periodo", "")
    marco = state.get("marco", "")

    escalaciones: list = []
    notif_por_owner: dict = {}
    for f in faltantes:
        notif_por_owner.setdefault(f["owner"], []).append(f)

    for owner, items in notif_por_owner.items():
        cuerpo = (
            f"AUDITORÍA {audit_id} ({marco}) — Periodo {periodo}\n"
            f"Se requiere evidencia faltante para los siguientes controles "
            f"a tu cargo (criticidad alta):\n"
        )
        for it in items:
            cuerpo += f"  · {it['control_id']} ({it['titulo']}) — tipo: {it['tipo_evidencia']}\n"
        cuerpo += (
            "\nFavor entregar evidencia ANTES del cierre de auditoría. "
            "Esta notificación queda registrada en la cadena de custodia."
        )
        escalaciones.append({
            "owner": owner,
            "controles": [it["control_id"] for it in items],
            "total_items": len(items),
            "asunto": f"[Compliance] Evidencia faltante {audit_id} — {marco}",
            "cuerpo": cuerpo,
            "canal": "email",
        })

    traza = _append_traza(state.get("trazabilidad", []), "escalar_responsable", {
        "total_escalaciones": len(escalaciones),
        "owners_notificados": list(notif_por_owner.keys()),
    })

    logger.info(
        "Escalaciones generadas: %d notificaciones a %d owners",
        len(escalaciones), len(notif_por_owner),
    )

    return {
        "escalaciones": escalaciones,
        "trazabilidad": traza,
        "events": [{
            "type": "responsables_escalados",
            "total_escalaciones": len(escalaciones),
            "owners": list(notif_por_owner.keys()),
        }],
    }


def validar_evidencias(state: ComplianceState) -> dict:
    """Verifica fechas dentro de periodo, campos obligatorios y sistemas válidos."""
    rules = get_validation_rules(get_data_dir())
    obligatorios = rules.get("campos_obligatorios", [])
    sistemas_validos = set(rules.get("sistemas_validos", []))
    max_antig = rules.get("max_antiguedad_dias", 365)
    alerta_antig = rules.get("antiguedad_alerta_dias", 180)
    periodo = state.get("periodo", "")
    p_start, p_end = _periodo_bounds(periodo)

    validaciones: list = []
    invalidas: list = []
    hoy = datetime.utcnow()

    for ev in state.get("evidencias", []):
        problemas: list = []
        for c in obligatorios:
            if not ev.get(c):
                problemas.append(f"campo_obligatorio_faltante:{c}")
        if ev.get("sistema") and ev["sistema"] not in sistemas_validos:
            problemas.append(f"sistema_invalido:{ev['sistema']}")

        f_dt = _parse_date(ev.get("fecha", ""))
        antig_dias = (hoy - f_dt).days if f_dt else None
        if f_dt is None:
            problemas.append("fecha_invalida")
        else:
            if antig_dias is not None and antig_dias > max_antig:
                problemas.append(f"evidencia_vencida:{antig_dias}d")
            if p_start and p_end and not (p_start <= f_dt <= p_end):
                # Solo se considera fuera-de-periodo problema si la evidencia es vieja.
                if antig_dias is not None and antig_dias > alerta_antig:
                    problemas.append("fuera_de_periodo_y_antigua")

        valido = not problemas
        v = {
            "control_id": ev.get("control"),
            "tipo": ev.get("tipo"),
            "ref": ev.get("ref"),
            "fecha": ev.get("fecha"),
            "antiguedad_dias": antig_dias,
            "valido": valido,
            "problemas": problemas,
        }
        validaciones.append(v)
        if not valido:
            invalidas.append(v)

    traza = _append_traza(state.get("trazabilidad", []), "validar_evidencias", {
        "total_validadas": len(validaciones),
        "validas": len(validaciones) - len(invalidas),
        "invalidas": len(invalidas),
    })

    logger.info(
        "Validación de evidencias: total=%d válidas=%d inválidas=%d",
        len(validaciones), len(validaciones) - len(invalidas), len(invalidas),
    )

    return {
        "validaciones": validaciones,
        "invalidas": invalidas,
        "trazabilidad": traza,
        "events": [{
            "type": "evidencias_validadas",
            "total_validadas": len(validaciones),
            "invalidas": len(invalidas),
        }],
    }


def generar_expediente(state: ComplianceState) -> dict:
    """Compila el expediente: índice por control + métricas + score de cumplimiento."""
    rules = get_validation_rules(get_data_dir())
    umbrales = rules.get("umbral_riesgo", {"verde_min_score": 95, "amarillo_min_score": 75})

    mapeo = state.get("mapeo_controles", [])
    cobertura = state.get("cobertura", {})
    invalidas = state.get("invalidas", [])
    invalidas_por_ctl: dict = {}
    for v in invalidas:
        invalidas_por_ctl.setdefault(v["control_id"], []).append(v)

    indice_por_control: list = []
    controles_completos = 0
    controles_parciales = 0
    controles_sin_evidencia = 0

    for ctl in mapeo:
        cid = ctl["control_id"]
        cov = cobertura.get(cid, {"requeridas": 0, "recibidas": 0})
        req = cov.get("requeridas", 0)
        rec = cov.get("recibidas", 0)
        invs = invalidas_por_ctl.get(cid, [])
        estado = "completo" if (req == rec and not invs) else (
            "sin_evidencia" if rec == 0 else "parcial"
        )
        if estado == "completo":
            controles_completos += 1
        elif estado == "sin_evidencia":
            controles_sin_evidencia += 1
        else:
            controles_parciales += 1

        indice_por_control.append({
            "control_id": cid,
            "titulo": ctl.get("titulo"),
            "criticidad": ctl.get("criticidad"),
            "owner": ctl.get("owner"),
            "estado": estado,
            "requeridas": req,
            "recibidas": rec,
            "invalidas": len(invs),
        })

    total_ctl = max(len(mapeo), 1)
    score = round(
        (controles_completos * 100 + controles_parciales * 50) / total_ctl
    )

    if score >= umbrales.get("verde_min_score", 95) and controles_sin_evidencia == 0:
        riesgo = "verde"
    elif score >= umbrales.get("amarillo_min_score", 75):
        riesgo = "amarillo"
    else:
        riesgo = "rojo"

    metricas = {
        "score_cumplimiento": score,
        "total_controles": len(mapeo),
        "controles_completos": controles_completos,
        "controles_parciales": controles_parciales,
        "controles_sin_evidencia": controles_sin_evidencia,
        "evidencias_validas": len(state.get("validaciones", [])) - len(invalidas),
        "evidencias_invalidas": len(invalidas),
        "faltantes": len(state.get("faltantes", [])),
        "escalaciones": len(state.get("escalaciones", [])),
    }

    expediente = {
        "audit_id": state.get("audit_id"),
        "marco": state.get("marco"),
        "marco_nombre": state.get("marco_nombre"),
        "periodo": state.get("periodo"),
        "descripcion": state.get("descripcion_escenario"),
        "score_cumplimiento": score,
        "riesgo": riesgo,
        "metricas": metricas,
        "indice_por_control": indice_por_control,
        "evidencias_anexas": state.get("evidencias", []),
        "validaciones": state.get("validaciones", []),
        "faltantes": state.get("faltantes", []),
        "escalaciones": state.get("escalaciones", []),
        "generado_en": _now_iso(),
    }

    traza = _append_traza(state.get("trazabilidad", []), "generar_expediente", {
        "score": score,
        "riesgo": riesgo,
        "controles_completos": controles_completos,
        "controles_parciales": controles_parciales,
        "controles_sin_evidencia": controles_sin_evidencia,
    })

    logger.info(
        "Expediente generado: score=%d riesgo=%s completos=%d parciales=%d sin=%d",
        score, riesgo, controles_completos, controles_parciales, controles_sin_evidencia,
    )

    return {
        "expediente": expediente,
        "score_cumplimiento": score,
        "riesgo": riesgo,
        "metricas": metricas,
        "trazabilidad": traza,
        "events": [{
            "type": "expediente_generado",
            "score": score,
            "riesgo": riesgo,
            "controles_completos": controles_completos,
            "controles_parciales": controles_parciales,
            "controles_sin_evidencia": controles_sin_evidencia,
        }],
    }


def log_trazabilidad(state: ComplianceState) -> dict:
    """Sella el cierre del expediente en la cadena de custodia."""
    traza = _append_traza(state.get("trazabilidad", []), "sellar_expediente", {
        "audit_id": state.get("audit_id"),
        "score": state.get("score_cumplimiento"),
        "riesgo": state.get("riesgo"),
        "total_entradas_previas": len(state.get("trazabilidad", [])),
    })

    logger.info(
        "Trazabilidad sellada: %d entradas, hash final=%s",
        len(traza), traza[-1]["hash"][:12],
    )

    return {
        "trazabilidad": traza,
        "events": [{
            "type": "trazabilidad_sellada",
            "total_entradas": len(traza),
            "hash_final": traza[-1]["hash"],
        }],
    }


def producir_resumen(state: ComplianceState) -> dict:
    """Resumen ejecutivo para el CISO/DPO/Compliance Officer."""
    metricas = state.get("metricas", {})
    audit_id = state.get("audit_id", "")
    marco_nombre = state.get("marco_nombre", "")
    periodo = state.get("periodo", "")
    score = state.get("score_cumplimiento", 0)
    riesgo = state.get("riesgo", "")
    riesgo_label = {"verde": "BAJO", "amarillo": "MEDIO", "rojo": "ALTO"}.get(riesgo, riesgo.upper())

    fallback = (
        f"## Resumen de auditoría — {audit_id} · {marco_nombre} · {periodo}\n\n"
        f"**Cumplimiento:** {score}/100 · **Riesgo regulatorio:** {riesgo_label}\n\n"
        f"### Estado de los controles\n"
        f"- Controles completos: {metricas.get('controles_completos', 0)}/{metricas.get('total_controles', 0)}\n"
        f"- Controles parciales: {metricas.get('controles_parciales', 0)}\n"
        f"- Controles sin evidencia: {metricas.get('controles_sin_evidencia', 0)}\n"
        f"- Evidencias inválidas: {metricas.get('evidencias_invalidas', 0)}\n"
        f"- Escalaciones a responsables: {metricas.get('escalaciones', 0)}\n\n"
        f"### Próximos pasos\n"
        f"- Recolectar las {metricas.get('faltantes', 0)} evidencias faltantes antes del cierre.\n"
        f"- Subsanar evidencias inválidas (fecha fuera de período / vencida).\n"
        f"- Validar respuesta de los responsables escalados.\n\n"
        f"_Expediente con cadena de custodia SHA-256 sellada. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres CISO. Redacta un resumen ejecutivo en español (máx 200 palabras) "
            f"para el comité de auditoría sobre la auditoría {audit_id} del marco {marco_nombre} "
            f"periodo {periodo}. Score de cumplimiento {score}/100, riesgo {riesgo_label}, "
            f"{metricas.get('controles_completos', 0)} controles completos de "
            f"{metricas.get('total_controles', 0)}, {metricas.get('escalaciones', 0)} escalaciones, "
            f"{metricas.get('evidencias_invalidas', 0)} evidencias inválidas. "
            f"Sé directo, orientado a decisión, cierra con próximos pasos concretos."
        )
        resumen = _llm_invoke(prompt, fallback)
    else:
        resumen = fallback

    logger.info(
        "Resumen generado: audit=%s marco=%s score=%s riesgo=%s modo=%s",
        audit_id, state.get("marco"), score, riesgo, "LIVE" if _LIVE_MODE else "DEMO",
    )

    return {
        "resumen": resumen,
        "done": True,
        "events": [{
            "type": "auditoria_completada",
            "audit_id": audit_id,
            "score": score,
            "riesgo": riesgo,
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(ComplianceState)

    builder.add_node("parsear_alcance", parsear_alcance)
    builder.add_node("mapear_controles", mapear_controles)
    builder.add_node("recopilar_evidencias", recopilar_evidencias)
    builder.add_node("escalar_responsable", escalar_responsable)
    builder.add_node("validar_evidencias", validar_evidencias)
    builder.add_node("generar_expediente", generar_expediente)
    builder.add_node("log_trazabilidad", log_trazabilidad)
    builder.add_node("producir_resumen", producir_resumen)

    builder.set_entry_point("parsear_alcance")
    builder.add_edge("parsear_alcance", "mapear_controles")
    builder.add_edge("mapear_controles", "recopilar_evidencias")

    builder.add_conditional_edges(
        "recopilar_evidencias",
        verificar_completitud,
        {
            "escalar_responsable": "escalar_responsable",
            "validar_evidencias": "validar_evidencias",
        },
    )
    builder.add_edge("escalar_responsable", "validar_evidencias")
    builder.add_edge("validar_evidencias", "generar_expediente")
    builder.add_edge("generar_expediente", "log_trazabilidad")
    builder.add_edge("log_trazabilidad", "producir_resumen")
    builder.add_edge("producir_resumen", END)

    return builder.compile(checkpointer=MemorySaver())
