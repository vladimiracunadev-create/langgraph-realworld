"""
integrations.py — Adaptadores de datos para Caso 06 (Compliance & Auditorías).

DEMO: lectura local de marcos.json, escenarios.json, validation_rules.json.
LIVE: en una integración real este módulo encapsularía clientes hacia
ServiceNow GRC, Jira, Confluence, GitHub Advanced Security, Splunk, AWS Config,
Okta y un GRC central (Vanta/Drata/SecureFrame).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo leer %s: %s", path.name, exc)
        return fallback


def get_marcos(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "marcos.json", {})


def get_validation_rules(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "validation_rules.json", {})


def get_escenario(audit_id: str, data_dir: str) -> dict:
    escenarios = _load_json(Path(data_dir) / "escenarios.json", [])
    for s in escenarios:
        if s.get("id") == audit_id:
            return s
    if escenarios:
        logger.info("audit_id=%s no encontrado; fallback al primero.", audit_id)
        return escenarios[0]
    return {
        "id": audit_id, "marco": "", "periodo": "", "descripcion": "",
        "controles_en_scope": [], "evidencias": [],
    }
