"""
integrations.py — Adaptadores de datos para Caso 14 (Finanzas: Conciliación).

DEMO: lectura local de scenarios.json, matching_rules.json, account_mapping.json.
LIVE: en una integración real este módulo encapsularía clientes de SAP/Oracle/Quickbooks
y conectores MT940/CAMT.053 para extractos bancarios estandarizados.
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


def get_scenario(scenario_id: str, data_dir: str) -> dict:
    scenarios = _load_json(Path(data_dir) / "scenarios.json", [])
    for s in scenarios:
        if s.get("id") == scenario_id:
            return s
    if scenarios:
        logger.info("scenario_id=%s no encontrado; fallback al primero.", scenario_id)
        return scenarios[0]
    return {
        "id": scenario_id, "periodo": "", "descripcion": "",
        "transacciones_bancarias": [], "transacciones_contables": [],
    }


def get_matching_rules(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "matching_rules.json", {})


def get_account_mapping(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "account_mapping.json", {})
