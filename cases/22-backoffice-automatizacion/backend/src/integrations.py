"""
integrations.py — Adaptadores de datos para Caso 22 (Backoffice Automatización).

DEMO: lectura local de solicitudes.json, empleados.json, operaciones_catalog.json, policy.json.
LIVE: un cliente real envolvería CRM (Salesforce), HRIS (Workday), Active Directory,
core bancario, IMAP/Webhooks de canales de entrada y un store append-only para auditoría.
"""
from __future__ import annotations

import hashlib
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


def get_solicitudes(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "solicitudes.json", [])


def get_solicitud(solicitud_id: str, data_dir: str) -> dict:
    items = get_solicitudes(data_dir)
    for s in items:
        if s.get("id") == solicitud_id:
            return s
    if items:
        logger.info("solicitud_id=%s no encontrada; fallback a la primera.", solicitud_id)
        return items[0]
    return {"id": solicitud_id, "canal": "desconocido", "solicitante_id": "",
            "tipo_operacion": "", "datos": {}, "prioridad": "normal", "descripcion": ""}


def get_empleados(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "empleados.json", [])


def get_empleado(empleado_id: str, data_dir: str) -> dict:
    for e in get_empleados(data_dir):
        if e.get("id") == empleado_id:
            return e
    return {}


def get_operaciones_catalog(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "operaciones_catalog.json", {})


def get_policy(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "policy.json", {})


def ejecutar_operacion_simulada(tipo: str, datos: dict, catalog: dict) -> dict:
    """Simulación determinista: éxito salvo que el catálogo marque `falla_simulada`."""
    cfg = catalog.get(tipo, {})
    if cfg.get("falla_simulada"):
        return {
            "ok": False,
            "sistema": cfg.get("sistema", "desconocido"),
            "endpoint": cfg.get("endpoint_simulado", ""),
            "error": "Timeout del sistema destino (simulado).",
        }
    return {
        "ok": True,
        "sistema": cfg.get("sistema", "desconocido"),
        "endpoint": cfg.get("endpoint_simulado", ""),
        "referencia": "REF-" + tipo[:4].upper() + "-" + hashlib.sha256(
            json.dumps(datos, sort_keys=True).encode("utf-8")
        ).hexdigest()[:8],
    }
