"""
integrations.py — Adaptadores de datos para Caso 07 (Compras y Abastecimiento).

DEMO: lectura local de scenarios.json, suppliers.json, procurement_policy.json.
LIVE: en una integración real este módulo encapsularía clientes de SAP MM,
Oracle Fusion Procurement, Coupa o Odoo, además de SendGrid/Microsoft Graph
para emisión de RFQs y firma digital de aprobaciones.
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
        "id": scenario_id,
        "centro_costo": "",
        "presupuesto_max": 0,
        "categoria": "",
        "descripcion": "",
        "items": [],
        "fecha_requerida": "",
        "responsable": "",
    }


def get_suppliers(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "suppliers.json", [])


def get_policy(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "procurement_policy.json", {})
