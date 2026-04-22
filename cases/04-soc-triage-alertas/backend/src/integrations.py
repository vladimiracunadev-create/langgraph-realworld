"""
integrations.py — Stubs de integración para Caso 04 (SOC Triage de Alertas).

En modo DEMO todas las funciones operan sobre los archivos JSON locales
(alerts.json, threat_intel.json) o devuelven respuestas simuladas realistas.
En modo LIVE se reemplazarían por llamadas a VirusTotal, AbuseIPDB, MISP,
Splunk/Elastic y JIRA/ServiceNow.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _alerts_path(data_dir: str) -> Path:
    return Path(data_dir) / "alerts.json"


def _threat_intel_path(data_dir: str) -> Path:
    return Path(data_dir) / "threat_intel.json"


def get_alert(alert_id: str, data_dir: str) -> dict:
    """
    Lee alerts.json y devuelve la alerta con el id dado.
    Si no existe, devuelve la primera como fallback DEMO.
    """
    path = _alerts_path(data_dir)
    try:
        alerts: list[dict] = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo leer alerts.json: %s", exc)
        return {
            "id": alert_id,
            "title": "Alerta DEMO",
            "source": "SIEM",
            "source_platform": "Splunk",
            "category": "unknown",
            "raw_severity": "medium",
            "host": "demo-host",
            "user": "demo-user",
            "src_ip": "192.0.2.1",
            "dst_ip": "10.0.0.1",
            "dst_port": 443,
            "iocs": ["192.0.2.1"],
            "event_count": 1,
            "first_seen": "2026-04-22T00:00:00Z",
            "last_seen": "2026-04-22T00:00:00Z",
            "raw_log": "Demo log entry",
            "tags": [],
        }

    for alert in alerts:
        if alert.get("id") == alert_id:
            return alert

    logger.info("alert_id=%s no encontrado; usando el primero como fallback.", alert_id)
    return alerts[0] if alerts else {}


def enrich_iocs(iocs: list[str], data_dir: str) -> dict:
    """
    Consulta threat intel para cada IOC (IP, hash, dominio).
    En modo DEMO lee threat_intel.json y devuelve lo que hay.
    En modo LIVE llamaría a VirusTotal, AbuseIPDB y MISP.
    """
    path = _threat_intel_path(data_dir)
    try:
        intel: dict = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo leer threat_intel.json: %s", exc)
        intel = {}

    results: dict[str, dict] = {}
    ip_rep = intel.get("ip_reputation", {})
    hashes = intel.get("file_hashes", {})
    domains = intel.get("domains", {})

    for ioc in iocs:
        if ioc in ip_rep:
            results[ioc] = {"type": "ip", **ip_rep[ioc]}
        elif ioc in hashes:
            results[ioc] = {"type": "hash", **hashes[ioc]}
        elif ioc in domains:
            results[ioc] = {"type": "domain", **domains[ioc]}
        else:
            results[ioc] = {"type": "unknown", "malicious": False, "score": 0, "sources": []}

    logger.info("DEMO: IOCs enriquecidos — %d consultados, %d con hits",
                len(iocs), sum(1 for v in results.values() if v.get("malicious")))
    return results


def get_mitre_mapping(tags: list[str], data_dir: str) -> list[dict]:
    """
    Devuelve el mapeo MITRE ATT&CK para los tags de la alerta.
    """
    path = _threat_intel_path(data_dir)
    try:
        intel: dict = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo leer threat_intel.json: %s", exc)
        return []

    mitre = intel.get("mitre_mapping", {})
    mappings = []
    for tag in tags:
        if tag in mitre:
            mappings.append({"tag": tag, **mitre[tag]})
    return mappings


def query_siem_context(host: str, user: str, time_window_hours: int = 24) -> dict:
    """
    Stub: consulta el SIEM para obtener contexto adicional del host/usuario.
    En modo DEMO devuelve datos simulados realistas.
    En modo LIVE ejecutaría queries SPL (Splunk) o KQL (Elastic).
    """
    logger.info("DEMO: Consultando SIEM — host=%s user=%s ventana=%dh", host, user, time_window_hours)
    return {
        "mode": "DEMO",
        "host": host,
        "user": user,
        "time_window_hours": time_window_hours,
        "related_events": 23,
        "failed_logins_24h": 5,
        "process_anomalies": 2,
        "data_transfer_mb": 12.4,
        "baseline_deviation_pct": 340,
        "note": "Actividad significativamente por encima del baseline del host",
    }


def assign_to_analyst(case: dict, priority: str) -> dict:
    """
    Stub: asigna el caso al analista SOC de turno.
    En modo DEMO simula la asignación sin llamar a JIRA/ServiceNow.
    En modo LIVE crearía un ticket en JIRA y notificaría vía Slack/PagerDuty.
    """
    analyst_map = {
        "critical": "analyst-oncall@empresa.com",
        "high": "analyst-senior@empresa.com",
        "medium": "analyst-l2@empresa.com",
    }
    assigned_to = analyst_map.get(priority, "analyst-l1@empresa.com")
    ticket_id = f"SOC-{case.get('id', 'DEMO')}-{priority[:3].upper()}"

    logger.info("DEMO: Caso asignado — ticket=%s analista=%s prioridad=%s",
                ticket_id, assigned_to, priority)
    return {
        "mode": "DEMO",
        "ticket_id": ticket_id,
        "assigned_to": assigned_to,
        "priority": priority,
        "status": "OPEN",
        "sla_hours": {"critical": 1, "high": 4, "medium": 8}.get(priority, 24),
    }


def close_false_positive(alert_id: str, reason: str) -> dict:
    """
    Stub: cierra la alerta como falso positivo con justificación auditada.
    En modo DEMO loguea la acción.
    En modo LIVE actualizaría el SIEM y el sistema de tickets.
    """
    logger.info("DEMO: Falso positivo cerrado — alert_id=%s reason=%s", alert_id, reason[:80])
    return {
        "mode": "DEMO",
        "alert_id": alert_id,
        "status": "CLOSED_FALSE_POSITIVE",
        "reason": reason,
        "closed_by": "SOC_AGENT_DEMO",
    }
