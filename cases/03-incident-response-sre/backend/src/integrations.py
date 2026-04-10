"""
integrations.py — Stubs de integración para Caso 03 (Incident Response SRE).

En modo DEMO (sin credenciales reales) todas las funciones operan sobre
los archivos JSON locales o devuelven respuestas simuladas.
En modo LIVE se reemplazarían por llamadas a PagerDuty, Prometheus, kubectl, etc.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def _incidents_path(data_dir: str) -> Path:
    return Path(data_dir) / "incidents.json"


def _runbooks_path(data_dir: str) -> Path:
    return Path(data_dir) / "runbooks.json"


def get_incident(incident_id: str, data_dir: str) -> dict:
    """
    Lee incidents.json y devuelve el incidente con el id dado.
    Si no existe el ID, devuelve el primero de la lista (fallback DEMO).
    """
    path = _incidents_path(data_dir)
    try:
        incidents: list[dict] = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo leer incidents.json: %s", exc)
        return {
            "id": incident_id,
            "title": "Incidente DEMO",
            "severity": "P2",
            "service": "demo-service",
            "description": "Incidente de demostración generado por fallback.",
            "metrics": {},
            "timestamp": "2026-04-09T00:00:00Z",
        }

    for inc in incidents:
        if inc.get("id") == incident_id:
            return inc

    # Fallback: primer incidente disponible
    logger.info("incident_id=%s no encontrado; usando el primero como fallback.", incident_id)
    return incidents[0] if incidents else {}


def get_runbook(severity: str, data_dir: str) -> dict:
    """
    Lee runbooks.json y devuelve el runbook para la severidad indicada (P1/P2/P3).
    Si la severidad no existe, devuelve el de P3 como fallback.
    """
    path = _runbooks_path(data_dir)
    try:
        runbooks: dict = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo leer runbooks.json: %s", exc)
        return {
            "steps": ["Revisar logs.", "Escalar al equipo de guardia."],
            "escalation_contact": "oncall@empresa.com",
        }

    key = severity.upper()
    if key in runbooks:
        return runbooks[key]

    logger.info("Severidad %s no encontrada en runbooks; usando P3 como fallback.", severity)
    return runbooks.get("P3", {})


def notify_pagerduty(incident: dict) -> dict:
    """
    Stub: notifica el incidente a PagerDuty.
    En modo DEMO loguea la acción sin hacer ninguna llamada HTTP real.
    """
    inc_id = incident.get("id", "N/A")
    severity = incident.get("severity", "N/A")
    service = incident.get("service", "N/A")
    logger.info(
        "DEMO: PagerDuty notificado — incident_id=%s severity=%s service=%s",
        inc_id, severity, service,
    )
    return {
        "notified": True,
        "mode": "DEMO",
        "incident_id": inc_id,
        "pagerduty_incident_key": f"demo-{inc_id.lower()}",
    }


def execute_remediation(actions: list[str]) -> dict:
    """
    Stub: ejecuta las acciones de remediación del runbook.
    En modo DEMO devuelve cada acción marcada como 'DEMO_executed'.
    """
    results: dict[str, str] = {}
    for action in actions:
        key = action[:60].replace(" ", "_")
        results[key] = "DEMO_executed"
        logger.info("DEMO: Acción ejecutada — %s", action[:80])
    return {"mode": "DEMO", "results": results, "total_actions": len(actions)}


def check_recovery(service: str) -> dict:
    """
    Stub: comprueba que el servicio se recuperó.
    En modo DEMO siempre devuelve recuperación exitosa.
    """
    logger.info("DEMO: Verificando recuperación del servicio %s", service)
    return {
        "service": service,
        "recovered": True,
        "mode": "DEMO",
        "checks": ["cpu_ok", "latency_ok", "error_rate_ok"],
    }
