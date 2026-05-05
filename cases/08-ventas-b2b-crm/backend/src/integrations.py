"""
integrations.py — Adaptadores de datos para Caso 08 (Ventas B2B + CRM).

Modo DEMO: lectura local de accounts.json, icp.json, outreach_templates.json,
responses.json, sales_reps.json.
Modo LIVE: en una integración real este módulo encapsularía clientes de
HubSpot/Salesforce/Pipedrive, Apollo.io/Clearbit y SendGrid/Microsoft Graph.
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


def get_account(account_id: str, data_dir: str) -> dict:
    accounts = _load_json(Path(data_dir) / "accounts.json", [])
    for a in accounts:
        if a.get("id") == account_id:
            return a
    if accounts:
        logger.info("account_id=%s no encontrado; fallback al primero.", account_id)
        return accounts[0]
    return {}


def get_icp(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "icp.json", {})


def get_templates(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "outreach_templates.json", {})


def get_responses(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "responses.json", {})


def get_sales_reps(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "sales_reps.json", [])


def render_template(template: str, variables: dict) -> str:
    out = template
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        if placeholder in out:
            out = out.replace(placeholder, str(value) if value else "{{PENDIENTE: " + key + "}}")
    return out
