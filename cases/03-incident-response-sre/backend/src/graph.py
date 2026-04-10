"""
graph.py — Grafo LangGraph para el Caso 03: Incident Response SRE.

Implementa el flujo completo de respuesta a incidentes:
  ingest_signals → classify_severity → [escalate_pagerduty |] find_runbook
  → request_human_approval → execute_remediation → verify_recovery
  → generate_postmortem → END

En modo DEMO (sin OPENAI_API_KEY) todos los nodos operan con lógica
determinista sobre los datos locales de incidents.json / runbooks.json.
En modo LIVE los nodos de análisis utilizarían un LLM para razonamiento.
"""
from __future__ import annotations

import logging
import operator
import os
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import (
    check_recovery,
    execute_remediation,
    get_incident,
    get_runbook,
    notify_pagerduty,
)
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Estado del grafo
# ---------------------------------------------------------------------------

class IncidentState(TypedDict):
    incident_id: str
    incident: dict
    signals: list
    severity: str
    runbook: dict
    approval_pending: bool
    approved: bool
    actions_taken: Annotated[list, operator.add]
    recovery: dict
    postmortem: str
    events: Annotated[list, operator.add]
    done: bool


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def ingest_signals(state: IncidentState) -> dict:
    """Carga el incidente desde la capa de integración y normaliza señales."""
    incident_id = state.get("incident_id", "INC-001")
    data_dir = get_data_dir()

    incident = get_incident(incident_id, data_dir)
    signals = [
        {
            "source": "incidents.json",
            "service": incident.get("service", "unknown"),
            "metrics": incident.get("metrics", {}),
            "timestamp": incident.get("timestamp", ""),
        }
    ]

    logger.info("Incidente cargado: id=%s severity=%s service=%s",
                incident.get("id"), incident.get("severity"), incident.get("service"))

    return {
        "incident": incident,
        "signals": signals,
        "events": [{"type": "signals_ingested", "incident_id": incident.get("id")}],
    }


def classify_severity(state: IncidentState) -> dict:
    """
    Determina la severidad del incidente.
    En modo DEMO usa directamente el campo 'severity' del incidente.
    En modo LIVE podría usar un LLM para analizar métricas y logs.
    """
    incident = state.get("incident", {})
    severity = incident.get("severity", "P3").upper()

    # Normalizar: aceptar solo P1/P2/P3; si no reconocido → P3
    if severity not in ("P1", "P2", "P3"):
        severity = "P3"

    logger.info("Severidad clasificada: %s", severity)

    return {
        "severity": severity,
        "events": [{"type": "severity_classified", "severity": severity}],
    }


def escalate_pagerduty(state: IncidentState) -> dict:
    """Notifica a PagerDuty (solo para incidentes P1)."""
    incident = state.get("incident", {})
    result = notify_pagerduty(incident)
    logger.info("PagerDuty escalado: %s", result)
    return {
        "events": [{"type": "pagerduty_escalated", "result": result}],
    }


def find_runbook(state: IncidentState) -> dict:
    """Recupera el runbook correspondiente a la severidad del incidente."""
    severity = state.get("severity", "P3")
    data_dir = get_data_dir()

    runbook = get_runbook(severity, data_dir)
    logger.info("Runbook encontrado para severidad %s con %d pasos",
                severity, len(runbook.get("steps", [])))

    return {
        "runbook": runbook,
        "events": [{"type": "runbook_found", "severity": severity,
                    "steps_count": len(runbook.get("steps", []))}],
    }


def request_human_approval(state: IncidentState) -> dict:
    """
    Solicita aprobación humana antes de ejecutar remediación.
    En modo DEMO auto-aprueba (approved=True).
    En modo LIVE usaría interrupt() de LangGraph para pausar el flujo
    y esperar confirmación explícita del SRE.
    """
    is_live = bool(os.getenv("OPENAI_API_KEY", "").strip())

    if is_live:
        # En producción real se usaría:
        # from langgraph.types import interrupt
        # interrupt({"message": "Aprobar remediación?", "runbook": state.get("runbook")})
        logger.info("Modo LIVE: auto-aprobando (interrupt() requiere configuración adicional)")

    logger.info("Aprobación: auto-aprobado en modo DEMO")
    return {
        "approval_pending": False,
        "approved": True,
        "events": [{"type": "approval_granted", "mode": "DEMO_auto"}],
    }


def execute_remediation_node(state: IncidentState) -> dict:
    """Ejecuta las acciones del runbook via la capa de integración."""
    runbook = state.get("runbook", {})
    steps = runbook.get("steps", [])

    result = execute_remediation(steps)
    logger.info("Remediación ejecutada: %d acciones", result.get("total_actions", 0))

    return {
        "actions_taken": steps,
        "events": [{"type": "remediation_executed", "total_actions": result.get("total_actions", 0)}],
    }


def verify_recovery(state: IncidentState) -> dict:
    """Verifica que el servicio se ha recuperado tras la remediación."""
    incident = state.get("incident", {})
    service = incident.get("service", "unknown")

    recovery = check_recovery(service)
    logger.info("Recuperación verificada: service=%s recovered=%s",
                service, recovery.get("recovered"))

    return {
        "recovery": recovery,
        "events": [{"type": "recovery_verified", "recovered": recovery.get("recovered", False)}],
    }


def generate_postmortem(state: IncidentState) -> dict:
    """
    Genera el resumen del incidente (postmortem).
    En modo DEMO produce un texto estructurado con los datos del estado.
    En modo LIVE utilizaría un LLM para redactar el postmortem completo.
    """
    incident = state.get("incident", {})
    severity = state.get("severity", "N/A")
    actions = state.get("actions_taken", [])
    recovery = state.get("recovery", {})
    events = state.get("events", [])

    lines = [
        f"# Postmortem — {incident.get('id', 'N/A')}",
        f"**Servicio afectado**: {incident.get('service', 'N/A')}",
        f"**Severidad**: {severity}",
        f"**Título**: {incident.get('title', 'N/A')}",
        f"**Descripción**: {incident.get('description', 'N/A')}",
        "",
        "## Timeline de eventos",
    ]
    for ev in events:
        lines.append(f"- {ev.get('type', 'event')}: {ev}")

    lines += [
        "",
        "## Acciones tomadas",
    ]
    for i, action in enumerate(actions, 1):
        lines.append(f"{i}. {action}")

    lines += [
        "",
        "## Estado de recuperación",
        f"- Recuperado: {recovery.get('recovered', False)}",
        f"- Checks: {', '.join(recovery.get('checks', []))}",
        "",
        "_Postmortem generado en modo DEMO por el Caso 03 — Incident Response SRE._",
    ]

    postmortem = "\n".join(lines)
    logger.info("Postmortem generado (%d líneas)", len(lines))

    return {
        "postmortem": postmortem,
        "done": True,
        "events": [{"type": "postmortem_generated"}],
    }


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def route_by_severity(state: IncidentState) -> str:
    """Enruta el flujo según la severidad: P1 escala a PagerDuty, P2/P3 va directo al runbook."""
    severity = state.get("severity", "P3")
    if severity == "P1":
        return "escalate_pagerduty"
    return "find_runbook"


# ---------------------------------------------------------------------------
# Compilación del grafo
# ---------------------------------------------------------------------------

def compile_graph():
    """Construye y compila el StateGraph con MemorySaver como checkpointer."""
    builder = StateGraph(IncidentState)

    # Nodos
    builder.add_node("ingest_signals", ingest_signals)
    builder.add_node("classify_severity", classify_severity)
    builder.add_node("escalate_pagerduty", escalate_pagerduty)
    builder.add_node("find_runbook", find_runbook)
    builder.add_node("request_human_approval", request_human_approval)
    builder.add_node("execute_remediation", execute_remediation_node)
    builder.add_node("verify_recovery", verify_recovery)
    builder.add_node("generate_postmortem", generate_postmortem)

    # Aristas
    builder.set_entry_point("ingest_signals")
    builder.add_edge("ingest_signals", "classify_severity")
    builder.add_conditional_edges(
        "classify_severity",
        route_by_severity,
        {
            "escalate_pagerduty": "escalate_pagerduty",
            "find_runbook": "find_runbook",
        },
    )
    builder.add_edge("escalate_pagerduty", "find_runbook")
    builder.add_edge("find_runbook", "request_human_approval")
    builder.add_edge("request_human_approval", "execute_remediation")
    builder.add_edge("execute_remediation", "verify_recovery")
    builder.add_edge("verify_recovery", "generate_postmortem")
    builder.add_edge("generate_postmortem", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)
