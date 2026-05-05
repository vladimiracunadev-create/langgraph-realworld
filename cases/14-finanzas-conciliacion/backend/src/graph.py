"""
graph.py — Grafo LangGraph para el Caso 14: Finanzas - Conciliación.

Pipeline de cierre y conciliación:
  normalizar_transacciones → clasificar_transacciones → matching_automatico
    → detectar_outliers
        ├─ error_contable      → proponer_ajuste            ┐
        ├─ posible_fraude      → escalar_auditoria          ├─→ generar_reporte_cuadre
        └─ partida_en_transito → marcar_partida_en_transito ┘
                                                                 ↓
                                                          producir_resumen → END

Detección de outliers determinista (z-score sobre histórico del propio escenario)
sin dependencias numéricas externas. LIVE opt-in con OPENAI_API_KEY para
justificación contable y resumen ejecutivo.
"""
from __future__ import annotations

import logging
import math
import operator
import os
from datetime import datetime
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import get_account_mapping, get_matching_rules, get_scenario
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class ConciliacionState(TypedDict):
    scenario_id: str
    periodo: str
    descripcion_escenario: str
    transacciones_bancarias: list
    transacciones_contables: list
    normalizadas_banco: list
    normalizadas_contables: list
    clasificaciones: dict
    matches: list
    unmatched_banco: list
    unmatched_contables: list
    outliers: list
    ajustes_propuestos: list
    escalaciones_auditoria: list
    partidas_en_transito: list
    metricas: dict
    reporte_cuadre: str
    resumen: str
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


# ---------------------------------------------------------------------------
# Helpers numéricos puros
# ---------------------------------------------------------------------------

def _parse_date(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        return None


def _zscore(values: list[float]) -> dict[int, float]:
    """Devuelve {idx: zscore} para una lista de valores."""
    if len(values) < 3:
        return {i: 0.0 for i in range(len(values))}
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = math.sqrt(variance) if variance > 0 else 1.0
    return {i: (v - mean) / std for i, v in enumerate(values)}


def _classify_tx(descripcion: str, contraparte: str, mapping: dict) -> dict:
    text = (descripcion + " " + contraparte).lower()
    for cat, info in mapping.get("categorias", {}).items():
        if cat == "otros":
            continue
        for kw in info.get("keywords", []):
            if kw.lower() in text:
                return {
                    "categoria": cat,
                    "cuenta_contable": info.get("cuenta", ""),
                    "centro_costo": info.get("centro_costo", ""),
                    "match_keyword": kw,
                }
    otros = mapping.get("categorias", {}).get("otros", {})
    return {
        "categoria": "otros",
        "cuenta_contable": otros.get("cuenta", "5999 - Otros Gastos"),
        "centro_costo": otros.get("centro_costo", "ADM"),
        "match_keyword": None,
    }


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def normalizar_transacciones(state: ConciliacionState) -> dict:
    """Carga el escenario y normaliza claves estándar."""
    scenario_id = state.get("scenario_id", "SCN-001")
    sc = get_scenario(scenario_id, get_data_dir())

    bancarias = sc.get("transacciones_bancarias", [])
    contables = sc.get("transacciones_contables", [])

    def _norm(tx_list):
        out = []
        for t in tx_list:
            out.append({
                "id": t.get("id", ""),
                "fecha": t.get("fecha", ""),
                "monto": float(t.get("monto", 0)),
                "descripcion": (t.get("descripcion") or "").strip(),
                "referencia": (t.get("referencia") or "").strip(),
                "contraparte": (t.get("contraparte") or "").strip(),
            })
        return out

    norm_banco = _norm(bancarias)
    norm_acct = _norm(contables)

    logger.info(
        "Transacciones normalizadas: banco=%d contables=%d periodo=%s",
        len(norm_banco), len(norm_acct), sc.get("periodo"),
    )

    return {
        "periodo": sc.get("periodo", ""),
        "descripcion_escenario": sc.get("descripcion", ""),
        "transacciones_bancarias": bancarias,
        "transacciones_contables": contables,
        "normalizadas_banco": norm_banco,
        "normalizadas_contables": norm_acct,
        "events": [{
            "type": "transacciones_normalizadas",
            "scenario_id": scenario_id,
            "periodo": sc.get("periodo"),
            "total_banco": len(norm_banco),
            "total_contable": len(norm_acct),
        }],
    }


def clasificar_transacciones(state: ConciliacionState) -> dict:
    """Asigna cuenta contable, centro de costo y categoría a cada movimiento."""
    mapping = get_account_mapping(get_data_dir())
    todas = state.get("normalizadas_banco", []) + state.get("normalizadas_contables", [])

    clasificaciones: dict = {}
    cat_counts: dict = {}
    for t in todas:
        c = _classify_tx(t["descripcion"], t["contraparte"], mapping)
        clasificaciones[t["id"]] = c
        cat_counts[c["categoria"]] = cat_counts.get(c["categoria"], 0) + 1

    logger.info("Clasificación: %d transacciones, categorías: %s", len(clasificaciones), cat_counts)

    return {
        "clasificaciones": clasificaciones,
        "events": [{
            "type": "transacciones_clasificadas",
            "total_clasificadas": len(clasificaciones),
            "distribucion_categorias": cat_counts,
        }],
    }


def matching_automatico(state: ConciliacionState) -> dict:
    """
    Empareja transacciones bancarias con contables aplicando reglas
    de score (referencia, fecha, monto, contraparte).
    """
    rules = get_matching_rules(get_data_dir())
    tol_monto = rules.get("tolerancia_monto_pesos", 1000)
    tol_fecha_exact = rules.get("tolerancia_fecha_dias_exacto", 1)
    tol_fecha_ampl = rules.get("tolerancia_fecha_dias_amplia", 3)
    umbral = rules.get("umbral_match_aceptable", 0.6)

    banco = state.get("normalizadas_banco", [])
    contables = state.get("normalizadas_contables", [])

    used_acct: set[str] = set()
    matches: list = []

    for b in banco:
        b_date = _parse_date(b["fecha"])
        best = None
        for a in contables:
            if a["id"] in used_acct:
                continue
            if abs(a["monto"] - b["monto"]) > tol_monto:
                continue
            a_date = _parse_date(a["fecha"])
            dias = abs((b_date - a_date).days) if (b_date and a_date) else 999
            ref_eq = (b["referencia"] and a["referencia"]
                      and b["referencia"].lower() == a["referencia"].lower())
            cp_eq = (b["contraparte"] and a["contraparte"]
                     and b["contraparte"].lower() == a["contraparte"].lower())

            score = 0.0
            criterio = ""
            if ref_eq and dias <= tol_fecha_exact:
                score, criterio = 1.0, "exact_match"
            elif dias <= tol_fecha_ampl:
                score, criterio = 0.7, "monto_fecha_amplia"
            elif cp_eq:
                score, criterio = 0.6, "monto_contraparte"

            if score >= umbral and (best is None or score > best["score"]):
                best = {
                    "bank_id": b["id"], "acct_id": a["id"],
                    "score": score, "criterio": criterio,
                    "monto": b["monto"], "fecha_banco": b["fecha"],
                    "fecha_contable": a["fecha"],
                }
        if best:
            matches.append(best)
            used_acct.add(best["acct_id"])

    matched_bank_ids = {m["bank_id"] for m in matches}
    matched_acct_ids = {m["acct_id"] for m in matches}
    unmatched_banco = [b for b in banco if b["id"] not in matched_bank_ids]
    unmatched_contables = [a for a in contables if a["id"] not in matched_acct_ids]

    logger.info(
        "Matching: %d matches (%d bancarias, %d contables) — pendientes banco=%d contable=%d",
        len(matches), len(matched_bank_ids), len(matched_acct_ids),
        len(unmatched_banco), len(unmatched_contables),
    )

    return {
        "matches": matches,
        "unmatched_banco": unmatched_banco,
        "unmatched_contables": unmatched_contables,
        "events": [{
            "type": "matching_completado",
            "total_matches": len(matches),
            "exact_matches": sum(1 for m in matches if m["criterio"] == "exact_match"),
            "matches_amplios": sum(1 for m in matches if m["criterio"] == "monto_fecha_amplia"),
            "pendientes_banco": len(unmatched_banco),
            "pendientes_contable": len(unmatched_contables),
        }],
    }


def detectar_outliers(state: ConciliacionState) -> dict:
    """
    Clasifica las transacciones no conciliadas en:
      - posible_fraude (señales de banca offshore + monto alto + descripción atípica)
      - error_contable (z-score alto sobre histórico de su clasificación)
      - partida_en_transito (típicas de fin de período: cheques/depósitos en tránsito)
    """
    rules = get_matching_rules(get_data_dir())
    threshold_z = rules.get("outlier_zscore_threshold", 2.5)
    fraud_kw = [k.lower() for k in rules.get("fraud_signals", {}).get("contraparte_desconocida_keywords", [])]
    fraud_min = rules.get("fraud_signals", {}).get("monto_minimo_alerta", 20000000)
    fraud_desc_kw = [k.lower() for k in rules.get("fraud_signals", {}).get("descripcion_alerta_keywords", [])]

    unmatched_banco = state.get("unmatched_banco", [])
    unmatched_contables = state.get("unmatched_contables", [])

    # z-score sobre montos absolutos del lado bancario para detección estadística
    banco_amounts = [abs(t["monto"]) for t in state.get("normalizadas_banco", [])]
    z_idx = _zscore(banco_amounts)
    bank_z_by_id = {
        t["id"]: z_idx.get(i, 0.0)
        for i, t in enumerate(state.get("normalizadas_banco", []))
    }

    outliers: list = []
    matches = state.get("matches", [])
    matches_with_z = []

    for m in matches:
        z = bank_z_by_id.get(m["bank_id"], 0.0)
        if abs(z) >= threshold_z:
            matches_with_z.append({**m, "zscore": z})

    for tx in unmatched_banco:
        cp = (tx.get("contraparte") or "").lower()
        desc = (tx.get("descripcion") or "").lower()
        monto_abs = abs(tx["monto"])
        z = bank_z_by_id.get(tx["id"], 0.0)

        is_fraud = (
            any(k in cp for k in fraud_kw) or any(k in desc for k in fraud_kw)
            or any(k in desc for k in fraud_desc_kw)
        ) and monto_abs >= fraud_min

        if is_fraud:
            outliers.append({
                "tx_id": tx["id"], "lado": "banco", "tipo": "posible_fraude",
                "monto": tx["monto"], "fecha": tx["fecha"],
                "contraparte": tx["contraparte"], "descripcion": tx["descripcion"],
                "razon": "Contraparte/descripción con señales de fraude (offshore o transferencia atípica) + monto alto.",
                "severidad": "alta", "zscore": round(z, 2),
            })
        else:
            outliers.append({
                "tx_id": tx["id"], "lado": "banco", "tipo": "error_contable",
                "monto": tx["monto"], "fecha": tx["fecha"],
                "contraparte": tx["contraparte"], "descripcion": tx["descripcion"],
                "razon": "Sin contrapartida en libro contable. Posible error de digitación o registro tardío.",
                "severidad": "media" if abs(z) < threshold_z else "alta",
                "zscore": round(z, 2),
            })

    for tx in unmatched_contables:
        desc = (tx.get("descripcion") or "").lower()
        is_transito = any(k in desc for k in [
            "tránsito", "transito", "cheque emitido", "no cobrado", "depósito", "deposito en tránsito", "deposito"
        ])

        if is_transito:
            outliers.append({
                "tx_id": tx["id"], "lado": "contable", "tipo": "partida_en_transito",
                "monto": tx["monto"], "fecha": tx["fecha"],
                "contraparte": tx["contraparte"], "descripcion": tx["descripcion"],
                "razon": "Diferencia de timing legítima — cheque emitido o depósito pendiente de cobro al cierre.",
                "severidad": "baja", "zscore": 0.0,
            })
        else:
            outliers.append({
                "tx_id": tx["id"], "lado": "contable", "tipo": "error_contable",
                "monto": tx["monto"], "fecha": tx["fecha"],
                "contraparte": tx["contraparte"], "descripcion": tx["descripcion"],
                "razon": "Asiento contable sin movimiento bancario asociado. Revisar duplicidad o monto erróneo.",
                "severidad": "media", "zscore": 0.0,
            })

    counts = {
        "posible_fraude": sum(1 for o in outliers if o["tipo"] == "posible_fraude"),
        "error_contable": sum(1 for o in outliers if o["tipo"] == "error_contable"),
        "partida_en_transito": sum(1 for o in outliers if o["tipo"] == "partida_en_transito"),
    }

    logger.info(
        "Outliers detectados: %s — total=%d, matches con z>%.1f=%d",
        counts, len(outliers), threshold_z, len(matches_with_z),
    )

    return {
        "outliers": outliers,
        "events": [{
            "type": "outliers_detectados",
            "total": len(outliers),
            **{f"total_{k}": v for k, v in counts.items()},
            "zscore_threshold": threshold_z,
        }],
    }


def proponer_ajuste(state: ConciliacionState) -> dict:
    """Propone asiento contable de ajuste para los outliers tipo error_contable."""
    outliers = state.get("outliers", [])
    clasificaciones = state.get("clasificaciones", {})
    errores = [o for o in outliers if o["tipo"] == "error_contable"]

    ajustes: list = []
    for o in errores:
        clas = clasificaciones.get(o["tx_id"], {})
        cuenta = clas.get("cuenta_contable", "5999 - Otros Gastos")
        signo = "Debe" if o["monto"] < 0 else "Haber"
        contra = "Banco - Cuenta Corriente" if o["lado"] == "contable" else cuenta
        cuenta_origen = cuenta if o["lado"] == "contable" else "Banco - Cuenta Corriente"

        justificacion_demo = (
            f"Diferencia detectada en {o['tx_id']} ({o['descripcion'][:60]}). "
            f"Se propone regularizar mediante asiento de ajuste contra {cuenta_origen}."
        )
        if _LIVE_MODE:
            prompt = (
                f"Eres contador senior. Redacta una justificación contable formal (máx 60 palabras) "
                f"para el ajuste de la transacción {o['tx_id']} de monto {o['monto']:.0f}, "
                f"descripción «{o['descripcion']}». Lado: {o['lado']}. Razón: {o['razon']}."
            )
            justificacion = _llm_invoke(prompt, justificacion_demo)
        else:
            justificacion = justificacion_demo

        ajustes.append({
            "tx_id": o["tx_id"],
            "lado": o["lado"],
            "monto": o["monto"],
            "asiento_sugerido": {
                "tipo": signo,
                "cuenta_origen": cuenta_origen,
                "cuenta_destino": contra,
                "monto_abs": abs(o["monto"]),
            },
            "justificacion": justificacion,
            "severidad": o["severidad"],
        })

    logger.info("Ajustes propuestos: %d", len(ajustes))

    return {
        "ajustes_propuestos": ajustes,
        "events": [{
            "type": "ajustes_propuestos",
            "total": len(ajustes),
            "muestra": ajustes[0]["tx_id"] if ajustes else None,
        }],
    }


def escalar_auditoria(state: ConciliacionState) -> dict:
    """Genera la nota de escalación a auditoría interna para outliers de fraude."""
    outliers = state.get("outliers", [])
    sospechosos = [o for o in outliers if o["tipo"] == "posible_fraude"]

    escalaciones: list = []
    for o in sospechosos:
        nota = (
            f"⚠️ ESCALACIÓN AUDITORÍA INTERNA — {o['tx_id']}\n"
            f"Monto: {o['monto']:,.0f} CLP · Fecha: {o['fecha']}\n"
            f"Contraparte: {o['contraparte']}\n"
            f"Descripción: {o['descripcion']}\n"
            f"Motivo de escalación: {o['razon']}\n"
            f"Severidad: {o['severidad'].upper()} · z-score: {o.get('zscore', 0)}\n"
            f"Acción requerida: revisión inmediata por auditoría interna y compliance "
            f"antes del cierre del período."
        )
        escalaciones.append({
            "tx_id": o["tx_id"],
            "monto": o["monto"],
            "contraparte": o["contraparte"],
            "razon": o["razon"],
            "nota": nota,
            "severidad": o["severidad"],
        })

    logger.info("Escalaciones a auditoría: %d", len(escalaciones))

    return {
        "escalaciones_auditoria": escalaciones,
        "events": [{
            "type": "auditoria_escalada",
            "total": len(escalaciones),
            "monto_total_sospechoso": sum(abs(e["monto"]) for e in escalaciones),
        }],
    }


def marcar_partida_en_transito(state: ConciliacionState) -> dict:
    """Marca como partidas en tránsito las diferencias legítimas de timing."""
    outliers = state.get("outliers", [])
    transito = [o for o in outliers if o["tipo"] == "partida_en_transito"]

    partidas: list = []
    for o in transito:
        partidas.append({
            "tx_id": o["tx_id"],
            "fecha": o["fecha"],
            "monto": o["monto"],
            "contraparte": o["contraparte"],
            "descripcion": o["descripcion"],
            "estado": "EN_TRANSITO",
            "nota": (
                "Diferencia de timing legítima. Se espera regularización en el próximo período. "
                "No requiere ajuste contable; mantener trazabilidad para cierre siguiente."
            ),
        })

    logger.info("Partidas en tránsito marcadas: %d", len(partidas))

    return {
        "partidas_en_transito": partidas,
        "events": [{
            "type": "partidas_transito_marcadas",
            "total": len(partidas),
            "monto_total_transito": sum(abs(p["monto"]) for p in partidas),
        }],
    }


def generar_reporte_cuadre(state: ConciliacionState) -> dict:
    """Calcula métricas y arma el reporte de cuadre con indicadores de riesgo."""
    matches = state.get("matches", [])
    banco = state.get("normalizadas_banco", [])
    contable = state.get("normalizadas_contables", [])

    total_bancario = sum(abs(t["monto"]) for t in banco)
    total_contable = sum(abs(t["monto"]) for t in contable)
    monto_conciliado = sum(abs(m["monto"]) for m in matches)

    base = max(total_bancario, total_contable, 1.0)
    pct = round(monto_conciliado / base * 100, 1)

    monto_pendiente = abs(total_bancario - total_contable)

    riesgo = "verde"
    if state.get("escalaciones_auditoria"):
        riesgo = "rojo"
    elif state.get("ajustes_propuestos") and pct < 90:
        riesgo = "amarillo"
    elif pct < 95:
        riesgo = "amarillo"

    metricas = {
        "total_bancario": round(total_bancario, 0),
        "total_contable": round(total_contable, 0),
        "monto_conciliado": round(monto_conciliado, 0),
        "conciliado_pct": pct,
        "monto_pendiente": round(monto_pendiente, 0),
        "riesgo": riesgo,
        "total_matches": len(matches),
        "exact_matches": sum(1 for m in matches if m["criterio"] == "exact_match"),
        "ajustes_pendientes": len(state.get("ajustes_propuestos", [])),
        "escalaciones": len(state.get("escalaciones_auditoria", [])),
        "partidas_en_transito": len(state.get("partidas_en_transito", [])),
    }

    riesgo_label = {"verde": "🟢 BAJO", "amarillo": "🟡 MEDIO", "rojo": "🔴 ALTO"}[riesgo]

    reporte = (
        f"REPORTE DE CUADRE — Período {state.get('periodo', '')}\n"
        f"=================================================\n\n"
        f"Total bancario:    {metricas['total_bancario']:>16,.0f} CLP\n"
        f"Total contable:    {metricas['total_contable']:>16,.0f} CLP\n"
        f"Monto conciliado:  {metricas['monto_conciliado']:>16,.0f} CLP "
        f"({pct}%)\n"
        f"Monto pendiente:   {metricas['monto_pendiente']:>16,.0f} CLP\n\n"
        f"Matches automáticos: {metricas['total_matches']} (exactos: {metricas['exact_matches']})\n"
        f"Ajustes propuestos:  {metricas['ajustes_pendientes']}\n"
        f"Escalaciones:        {metricas['escalaciones']}\n"
        f"Partidas en tránsito: {metricas['partidas_en_transito']}\n\n"
        f"Indicador de riesgo: {riesgo_label}\n"
    )

    logger.info(
        "Reporte de cuadre: pct=%.1f%% riesgo=%s ajustes=%d escalaciones=%d",
        pct, riesgo,
        metricas["ajustes_pendientes"], metricas["escalaciones"],
    )

    return {
        "metricas": metricas,
        "reporte_cuadre": reporte,
        "events": [{
            "type": "reporte_generado",
            "conciliado_pct": pct,
            "riesgo": riesgo,
            "ajustes": metricas["ajustes_pendientes"],
            "escalaciones": metricas["escalaciones"],
        }],
    }


def producir_resumen(state: ConciliacionState) -> dict:
    """Resumen ejecutivo para el controller."""
    metricas = state.get("metricas", {})
    periodo = state.get("periodo", "")
    pct = metricas.get("conciliado_pct", 0)
    riesgo = metricas.get("riesgo", "")
    riesgo_label = {"verde": "BAJO", "amarillo": "MEDIO", "rojo": "ALTO"}.get(riesgo, riesgo.upper())

    fallback = (
        f"## Resumen de cierre — {periodo}\n\n"
        f"**Cuadre:** {pct}% conciliado · pendiente {metricas.get('monto_pendiente', 0):,.0f} CLP\n"
        f"**Riesgo:** {riesgo_label}\n\n"
        f"### Acciones requeridas\n"
        f"- Ajustes contables a aplicar: {metricas.get('ajustes_pendientes', 0)}\n"
        f"- Escalaciones a auditoría: {metricas.get('escalaciones', 0)}\n"
        f"- Partidas en tránsito a monitorear el próximo cierre: {metricas.get('partidas_en_transito', 0)}\n\n"
        f"_Reporte generado por agente de conciliación — Caso 14. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres CFO. Redacta un resumen ejecutivo en español (máx 200 palabras) para el controller "
            f"sobre el cierre del período {periodo}. Cuadre: {pct}%, riesgo {riesgo_label}, "
            f"{metricas.get('ajustes_pendientes', 0)} ajustes, "
            f"{metricas.get('escalaciones', 0)} escalaciones a auditoría. "
            f"Sé directo, orientado a decisión, cierra con próximos pasos concretos."
        )
        resumen = _llm_invoke(prompt, fallback)
    else:
        resumen = fallback

    logger.info(
        "Resumen generado: periodo=%s pct=%s riesgo=%s modo=%s",
        periodo, pct, riesgo, "LIVE" if _LIVE_MODE else "DEMO",
    )

    return {
        "resumen": resumen,
        "done": True,
        "events": [{
            "type": "cierre_completado",
            "periodo": periodo,
            "conciliado_pct": pct,
            "riesgo": riesgo,
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(ConciliacionState)

    builder.add_node("normalizar_transacciones", normalizar_transacciones)
    builder.add_node("clasificar_transacciones", clasificar_transacciones)
    builder.add_node("matching_automatico", matching_automatico)
    builder.add_node("detectar_outliers", detectar_outliers)
    builder.add_node("proponer_ajuste", proponer_ajuste)
    builder.add_node("escalar_auditoria", escalar_auditoria)
    builder.add_node("marcar_partida_en_transito", marcar_partida_en_transito)
    builder.add_node("generar_reporte_cuadre", generar_reporte_cuadre)
    builder.add_node("producir_resumen", producir_resumen)

    builder.set_entry_point("normalizar_transacciones")
    builder.add_edge("normalizar_transacciones", "clasificar_transacciones")
    builder.add_edge("clasificar_transacciones", "matching_automatico")
    builder.add_edge("matching_automatico", "detectar_outliers")

    # Las 3 ramas de discrepancia siempre se ejecutan en secuencia (procesan listas filtradas
    # del array outliers — si no hay del tipo correspondiente, el nodo es no-op pero
    # mantiene la traza de eventos limpia).
    builder.add_edge("detectar_outliers", "proponer_ajuste")
    builder.add_edge("proponer_ajuste", "escalar_auditoria")
    builder.add_edge("escalar_auditoria", "marcar_partida_en_transito")
    builder.add_edge("marcar_partida_en_transito", "generar_reporte_cuadre")
    builder.add_edge("generar_reporte_cuadre", "producir_resumen")
    builder.add_edge("producir_resumen", END)

    return builder.compile(checkpointer=MemorySaver())
