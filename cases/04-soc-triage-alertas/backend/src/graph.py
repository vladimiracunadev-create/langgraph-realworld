"""
graph.py — Grafo LangGraph para el Caso 04: SOC Triage de Alertas.

Implementa el flujo completo de triage en un Centro de Operaciones de Seguridad:
  normalizar_alerta → enriquecer_ioc → correlacionar_eventos → evaluar_riesgo
    ├─ falso_positivo  → cerrar_automatico → END
    ├─ riesgo_medio    → investigacion_adicional → decision_investigacion
    │                      ├─ benigno     → cerrar_automatico → END
    │                      └─ sospechoso  → escalar_analista → generar_informe_triage → END
    └─ riesgo_alto     → escalar_analista → generar_informe_triage → END

Modo DEMO (sin OPENAI_API_KEY): lógica determinista sobre datos locales.
Modo LIVE (con OPENAI_API_KEY): los nodos de análisis usan GPT-4o-mini para
razonamiento contextual sobre la alerta, los IOCs y el contexto SIEM.
"""
from __future__ import annotations

import logging
import operator
import os
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import (
    assign_to_analyst,
    close_false_positive,
    enrich_iocs,
    get_alert,
    get_mitre_mapping,
    query_siem_context,
)
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado del grafo
# ---------------------------------------------------------------------------

class AlertState(TypedDict):
    alert_id: str
    alert: dict                                     # alerta normalizada
    ioc_enrichment: dict                            # resultado de threat intel por IOC
    mitre_techniques: list                          # técnicas MITRE mapeadas
    siem_context: dict                              # contexto adicional del SIEM
    risk_score: int                                 # 0-100
    risk_level: str                                 # "low" | "medium" | "high" | "critical"
    triage_decision: str                            # "false_positive" | "medium" | "high"
    investigation_result: str                       # "benign" | "suspicious"
    analyst_assignment: dict                        # ticket + analista asignado
    close_record: dict                              # registro de cierre para FP
    triage_report: str                              # informe final para el analista
    events: Annotated[list, operator.add]           # timeline auditado
    done: bool


# ---------------------------------------------------------------------------
# Helper LLM (modo LIVE)
# ---------------------------------------------------------------------------

def _llm_analyze(prompt: str, fallback: str) -> str:
    """
    Invoca GPT-4o-mini si hay API key disponible.
    Si no, devuelve el fallback determinista para modo DEMO.
    """
    if not _LIVE_MODE:
        return fallback
    try:
        from langchain_openai import ChatOpenAI
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model_name, temperature=0)
        return llm.invoke(prompt).content
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM no disponible, usando fallback DEMO: %s", exc)
        return fallback


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def normalizar_alerta(state: AlertState) -> dict:
    """
    Carga la alerta desde la fuente (SIEM/EDR/Firewall) y la normaliza
    a un esquema común independiente de la plataforma de origen.
    """
    alert_id = state.get("alert_id", "ALT-001")
    data_dir = get_data_dir()

    alert = get_alert(alert_id, data_dir)

    # Normalizar severidad de texto libre a niveles estándar SOC
    raw_sev = alert.get("raw_severity", "medium").lower()
    severity_map = {"critical": "critical", "high": "high", "medium": "medium",
                    "low": "low", "info": "low"}
    alert["normalized_severity"] = severity_map.get(raw_sev, "medium")

    logger.info(
        "Alerta normalizada: id=%s source=%s category=%s severity=%s iocs=%d",
        alert.get("id"), alert.get("source"), alert.get("category"),
        alert.get("normalized_severity"), len(alert.get("iocs", [])),
    )

    return {
        "alert": alert,
        "events": [{"type": "alert_normalized", "alert_id": alert.get("id"),
                    "source": alert.get("source"), "category": alert.get("category")}],
    }


def enriquecer_ioc(state: AlertState) -> dict:
    """
    Consulta VirusTotal / AbuseIPDB / MISP para cada IOC de la alerta.
    En modo LIVE los resultados reales guían el score; en DEMO usa
    threat_intel.json local.
    """
    alert = state.get("alert", {})
    iocs = alert.get("iocs", [])
    data_dir = get_data_dir()

    enrichment = enrich_iocs(iocs, data_dir)
    mitre = get_mitre_mapping(alert.get("tags", []), data_dir)

    malicious_count = sum(1 for v in enrichment.values() if v.get("malicious"))
    max_score = max((v.get("score", 0) for v in enrichment.values()), default=0)

    logger.info(
        "IOCs enriquecidos: total=%d maliciosos=%d max_score=%d técnicas_MITRE=%d",
        len(iocs), malicious_count, max_score, len(mitre),
    )

    return {
        "ioc_enrichment": enrichment,
        "mitre_techniques": mitre,
        "events": [{"type": "ioc_enriched", "total_iocs": len(iocs),
                    "malicious_hits": malicious_count, "max_score": max_score,
                    "mitre_techniques": [m.get("technique") for m in mitre]}],
    }


def correlacionar_eventos(state: AlertState) -> dict:
    """
    Consulta el SIEM para obtener contexto adicional del host y usuario.
    Agrupa eventos relacionados por host/usuario/campaña.
    """
    alert = state.get("alert", {})
    host = alert.get("host", "unknown")
    user = alert.get("user") or "N/A"

    siem_ctx = query_siem_context(host, user)

    logger.info(
        "Contexto SIEM: host=%s eventos_relacionados=%d anomalías_proceso=%d desviación_baseline=%s%%",
        host, siem_ctx.get("related_events", 0),
        siem_ctx.get("process_anomalies", 0),
        siem_ctx.get("baseline_deviation_pct", 0),
    )

    return {
        "siem_context": siem_ctx,
        "events": [{"type": "events_correlated", "host": host,
                    "related_events": siem_ctx.get("related_events", 0),
                    "baseline_deviation_pct": siem_ctx.get("baseline_deviation_pct", 0)}],
    }


def evaluar_riesgo(state: AlertState) -> dict:
    """
    Calcula el score de riesgo compuesto (0-100) y determina la ruta de triage.

    Algoritmo (DEMO): pondera IOC reputation, baseline deviation, event count
    y severidad de la fuente. En modo LIVE el LLM razona sobre el contexto
    completo y puede ajustar el score con contexto de negocio.

    Resultado:
      score < 30   → falso_positivo
      30 ≤ score < 70 → riesgo_medio
      score ≥ 70   → riesgo_alto
    """
    alert = state.get("alert", {})
    enrichment = state.get("ioc_enrichment", {})
    siem_ctx = state.get("siem_context", {})

    # --- Score base por IOCs ---
    ioc_scores = [v.get("score", 0) for v in enrichment.values() if v.get("malicious")]
    ioc_component = min(int(sum(ioc_scores) / max(len(ioc_scores), 1) * 0.5), 50)

    # --- Score por comportamiento SIEM ---
    deviation = siem_ctx.get("baseline_deviation_pct", 0)
    siem_component = min(int(deviation / 20), 30)

    # --- Score por severidad de la fuente ---
    sev_map = {"critical": 20, "high": 15, "medium": 8, "low": 3}
    sev_component = sev_map.get(alert.get("normalized_severity", "medium"), 5)

    raw_score = ioc_component + siem_component + sev_component
    risk_score = min(raw_score, 100)

    # Ajuste LIVE: LLM puede justificar un incremento si el contexto lo amerita
    if _LIVE_MODE:
        prompt = (
            f"Eres un analista SOC senior. Revisa esta alerta y su contexto:\n\n"
            f"Alerta: {alert.get('title')}\nCategoría: {alert.get('category')}\n"
            f"Score calculado: {risk_score}/100\n"
            f"IOCs maliciosos: {sum(1 for v in enrichment.values() if v.get('malicious'))}\n"
            f"Técnicas MITRE: {[m.get('technique') for m in state.get('mitre_techniques', [])]}\n"
            f"Desviación baseline SIEM: {deviation}%\n\n"
            f"¿El score de {risk_score} es apropiado? Responde SOLO con un número del 0 al 100."
        )
        llm_score_str = _llm_analyze(prompt, str(risk_score))
        try:
            risk_score = max(0, min(100, int(llm_score_str.strip())))
        except ValueError:
            pass  # mantener el score calculado si LLM no devuelve número

    # Determinar nivel
    if risk_score < 30:
        risk_level = "low"
        decision = "false_positive"
    elif risk_score < 70:
        risk_level = "medium"
        decision = "medium"
    else:
        risk_level = "high" if risk_score < 90 else "critical"
        decision = "high"

    logger.info(
        "Riesgo evaluado: score=%d level=%s decision=%s (ioc=%d siem=%d sev=%d)",
        risk_score, risk_level, decision,
        ioc_component, siem_component, sev_component,
    )

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "triage_decision": decision,
        "events": [{"type": "risk_evaluated", "score": risk_score,
                    "level": risk_level, "decision": decision}],
    }


def cerrar_automatico(state: AlertState) -> dict:
    """
    Cierra la alerta como falso positivo con justificación auditada.
    Genera la razón en modo DEMO (determinista) o LIVE (LLM).
    """
    alert = state.get("alert", {})
    enrichment = state.get("ioc_enrichment", {})
    risk_score = state.get("risk_score", 0)

    fallback_reason = (
        f"Alerta '{alert.get('title')}' cerrada automáticamente como falso positivo. "
        f"Score de riesgo: {risk_score}/100 (umbral: 30). "
        f"IOCs sin hits maliciosos en threat intel. "
        f"Actividad dentro del baseline normal del host."
    )

    reason = _llm_analyze(
        f"Justifica en 2 frases por qué esta alerta SOC es un falso positivo:\n"
        f"Alerta: {alert.get('title')}\nScore: {risk_score}\n"
        f"IOCs: {list(enrichment.keys())}\nFuente: {alert.get('source')}",
        fallback_reason,
    )

    close_record = close_false_positive(alert.get("id", "ALT-DEMO"), reason)
    logger.info("Alerta cerrada como FP: %s", alert.get("id"))

    return {
        "close_record": close_record,
        "done": True,
        "events": [{"type": "closed_false_positive", "alert_id": alert.get("id"),
                    "score": risk_score, "reason_summary": reason[:100]}],
    }


def investigacion_adicional(state: AlertState) -> dict:
    """
    Ejecuta queries adicionales en el SIEM para obtener más contexto
    antes de tomar la decisión final en alertas de riesgo medio.
    En modo LIVE el LLM analiza el contexto ampliado.
    """
    alert = state.get("alert", {})
    siem_ctx = state.get("siem_context", {})
    enrichment = state.get("ioc_enrichment", {})

    # Contexto ampliado: ventana de 72h en lugar de 24h
    extended_ctx = query_siem_context(
        alert.get("host", "unknown"),
        alert.get("user") or "N/A",
        time_window_hours=72,
    )

    # Decisión DEMO: si hay IOCs maliciosos O alta desviación de baseline → sospechoso
    has_malicious_iocs = any(v.get("malicious") for v in enrichment.values())
    high_deviation = extended_ctx.get("baseline_deviation_pct", 0) > 200

    fallback_decision = "suspicious" if (has_malicious_iocs or high_deviation) else "benign"

    decision = _llm_analyze(
        f"Eres analista SOC L2. Tras investigación ampliada de 72h:\n"
        f"Alerta: {alert.get('title')}\nCategoría: {alert.get('category')}\n"
        f"IOCs maliciosos: {has_malicious_iocs}\n"
        f"Desviación baseline 72h: {extended_ctx.get('baseline_deviation_pct')}%\n"
        f"Eventos relacionados: {extended_ctx.get('related_events')}\n\n"
        f"¿Es 'suspicious' o 'benign'? Responde SOLO con una de esas dos palabras.",
        fallback_decision,
    ).strip().lower()

    if decision not in ("suspicious", "benign"):
        decision = fallback_decision

    logger.info(
        "Investigación adicional: alerta=%s decision=%s (ioc_malicioso=%s desviacion=%d%%)",
        alert.get("id"), decision, has_malicious_iocs,
        extended_ctx.get("baseline_deviation_pct", 0),
    )

    return {
        "siem_context": extended_ctx,
        "investigation_result": decision,
        "events": [{"type": "additional_investigation", "decision": decision,
                    "extended_window_h": 72,
                    "baseline_deviation_pct": extended_ctx.get("baseline_deviation_pct", 0)}],
    }


def escalar_analista(state: AlertState) -> dict:
    """
    Asigna el caso al analista SOC de turno según la prioridad.
    Crea ticket en sistema de tickets (JIRA/ServiceNow en LIVE).
    """
    alert = state.get("alert", {})
    risk_level = state.get("risk_level", "high")
    risk_score = state.get("risk_score", 0)

    # Mapeo level → priority para el sistema de tickets
    priority_map = {"critical": "critical", "high": "high", "medium": "medium", "low": "medium"}
    priority = priority_map.get(risk_level, "high")

    assignment = assign_to_analyst(alert, priority)

    logger.info(
        "Caso escalado: alert=%s priority=%s ticket=%s analista=%s SLA=%dh",
        alert.get("id"), priority,
        assignment.get("ticket_id"), assignment.get("assigned_to"),
        assignment.get("sla_hours", 0),
    )

    return {
        "analyst_assignment": assignment,
        "events": [{"type": "escalated_to_analyst", "ticket_id": assignment.get("ticket_id"),
                    "priority": priority, "sla_hours": assignment.get("sla_hours"),
                    "risk_score": risk_score}],
    }


def generar_informe_triage(state: AlertState) -> dict:
    """
    Produce el informe estructurado de triage con evidencias, contexto
    MITRE ATT&CK, IOCs enriquecidos y recomendaciones para el analista.
    En modo LIVE el LLM redacta un informe ejecutivo; en DEMO genera
    el informe estructurado con los datos disponibles.
    """
    alert = state.get("alert", {})
    enrichment = state.get("ioc_enrichment", {})
    mitre = state.get("mitre_techniques", [])
    siem_ctx = state.get("siem_context", {})
    assignment = state.get("analyst_assignment", {})
    risk_score = state.get("risk_score", 0)
    risk_level = state.get("risk_level", "high")
    events = state.get("events", [])

    # Fallback estructurado (DEMO)
    malicious_iocs = {k: v for k, v in enrichment.items() if v.get("malicious")}
    clean_iocs = {k: v for k, v in enrichment.items() if not v.get("malicious")}

    lines = [
        f"# Informe de Triage SOC — {alert.get('id', 'N/A')}",
        f"**Ticket**: {assignment.get('ticket_id', 'N/A')} | "
        f"**Analista**: {assignment.get('assigned_to', 'N/A')} | "
        f"**SLA**: {assignment.get('sla_hours', 'N/A')}h",
        "",
        "## Resumen ejecutivo",
        f"- **Alerta**: {alert.get('title')}",
        f"- **Fuente**: {alert.get('source')} / {alert.get('source_platform')}",
        f"- **Host afectado**: {alert.get('host')} | **Usuario**: {alert.get('user') or 'N/A'}",
        f"- **Score de riesgo**: {risk_score}/100 ({risk_level.upper()})",
        f"- **Categoría**: {alert.get('category')} | **Eventos**: {alert.get('event_count')}",
        f"- **Ventana**: {alert.get('first_seen')} → {alert.get('last_seen')}",
        "",
        "## IOCs con hits maliciosos",
    ]

    if malicious_iocs:
        for ioc, data in malicious_iocs.items():
            lines.append(
                f"- `{ioc}` → score={data.get('score')}, "
                f"categorías={data.get('categories', [])}, "
                f"fuentes={data.get('sources', [])}"
            )
    else:
        lines.append("- Ninguno detectado en bases de datos de threat intel.")

    if clean_iocs:
        lines += ["", "## IOCs sin hits (verificados benignos)"]
        for ioc in clean_iocs:
            lines.append(f"- `{ioc}`")

    lines += ["", "## Mapeo MITRE ATT&CK"]
    if mitre:
        for m in mitre:
            lines.append(
                f"- **{m.get('tactic')}** / {m.get('technique')}"
                + (f".{m.get('subtechnique', '')}" if m.get("subtechnique") else "")
                + f" (tag: `{m.get('tag')}`)"
            )
    else:
        lines.append("- No se encontraron técnicas mapeadas para los tags de esta alerta.")

    lines += [
        "",
        "## Contexto SIEM",
        f"- Eventos relacionados (72h): {siem_ctx.get('related_events', 'N/A')}",
        f"- Fallos de login (24h): {siem_ctx.get('failed_logins_24h', 'N/A')}",
        f"- Anomalías de proceso: {siem_ctx.get('process_anomalies', 'N/A')}",
        f"- Transferencia datos: {siem_ctx.get('data_transfer_mb', 'N/A')} MB",
        f"- Desviación baseline: {siem_ctx.get('baseline_deviation_pct', 'N/A')}%",
        "",
        "## Timeline de eventos del agente",
    ]
    for ev in events:
        lines.append(f"- `{ev.get('type', 'event')}`: {ev}")

    lines += [
        "",
        "## Acciones recomendadas",
        f"1. Revisar logs completos del host `{alert.get('host')}` en la ventana indicada.",
        "2. Verificar si el proceso/usuario tiene justificación de negocio.",
        "3. Correlacionar con tickets de cambio o actividad programada.",
        "4. Si se confirma compromiso: iniciar playbook de contención (Caso 03).",
        "",
        "_Informe generado automáticamente por el Agente SOC Triage — Caso 04._",
        f"_Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}_",
    ]

    fallback_report = "\n".join(lines)

    # En modo LIVE el LLM genera el resumen ejecutivo narrativo
    report = _llm_analyze(
        f"Eres analista SOC senior. Genera un informe de triage ejecutivo en español "
        f"basado en estos datos:\n\n{fallback_report[:2000]}\n\n"
        f"El informe debe incluir: resumen, evidencias clave, mapeo MITRE, "
        f"y 3 acciones inmediatas. Máximo 400 palabras.",
        fallback_report,
    )

    logger.info("Informe de triage generado: %d líneas, modo=%s",
                len(lines), "LIVE" if _LIVE_MODE else "DEMO")

    return {
        "triage_report": report,
        "done": True,
        "events": [{"type": "triage_report_generated",
                    "alert_id": alert.get("id"),
                    "ticket_id": assignment.get("ticket_id"),
                    "risk_score": risk_score}],
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

def route_by_risk(state: AlertState) -> str:
    """Primer router: según el nivel de riesgo decide la ruta de triage."""
    decision = state.get("triage_decision", "medium")
    routes = {
        "false_positive": "cerrar_automatico",
        "medium": "investigacion_adicional",
        "high": "escalar_analista",
    }
    return routes.get(decision, "escalar_analista")


def route_investigation(state: AlertState) -> str:
    """Segundo router: resultado de la investigación adicional."""
    result = state.get("investigation_result", "suspicious")
    if result == "benign":
        return "cerrar_automatico"
    return "escalar_analista"


# ---------------------------------------------------------------------------
# Compilación del grafo
# ---------------------------------------------------------------------------

def compile_graph():
    """Construye y compila el StateGraph con MemorySaver como checkpointer."""
    builder = StateGraph(AlertState)

    builder.add_node("normalizar_alerta", normalizar_alerta)
    builder.add_node("enriquecer_ioc", enriquecer_ioc)
    builder.add_node("correlacionar_eventos", correlacionar_eventos)
    builder.add_node("evaluar_riesgo", evaluar_riesgo)
    builder.add_node("cerrar_automatico", cerrar_automatico)
    builder.add_node("investigacion_adicional", investigacion_adicional)
    builder.add_node("escalar_analista", escalar_analista)
    builder.add_node("generar_informe_triage", generar_informe_triage)

    builder.set_entry_point("normalizar_alerta")
    builder.add_edge("normalizar_alerta", "enriquecer_ioc")
    builder.add_edge("enriquecer_ioc", "correlacionar_eventos")
    builder.add_edge("correlacionar_eventos", "evaluar_riesgo")

    builder.add_conditional_edges(
        "evaluar_riesgo",
        route_by_risk,
        {
            "cerrar_automatico": "cerrar_automatico",
            "investigacion_adicional": "investigacion_adicional",
            "escalar_analista": "escalar_analista",
        },
    )

    builder.add_conditional_edges(
        "investigacion_adicional",
        route_investigation,
        {
            "cerrar_automatico": "cerrar_automatico",
            "escalar_analista": "escalar_analista",
        },
    )

    builder.add_edge("cerrar_automatico", END)
    builder.add_edge("escalar_analista", "generar_informe_triage")
    builder.add_edge("generar_informe_triage", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)
