"""
integrations.py — Adaptadores de datos para Caso 24 (Asistente de Product Manager).

DEMO: lectura local de iniciativas.json, equipos.json, catalogo_estimacion.json, policy.json.
LIVE: un cliente real envolvería Jira/Linear/GitHub Projects, Slack/Teams para
notificaciones de impedimentos y una base de datos de productos/proyectos.
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


def get_iniciativas(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "iniciativas.json", [])


def get_iniciativa(iniciativa_id: str, data_dir: str) -> dict:
    items = get_iniciativas(data_dir)
    for i in items:
        if i.get("id") == iniciativa_id:
            return i
    if items:
        logger.info("iniciativa_id=%s no encontrada; fallback a la primera.", iniciativa_id)
        return items[0]
    return {
        "id": iniciativa_id, "titulo": "", "contexto": "",
        "stakeholders": [], "fuente": "idea", "equipo_id": "",
        "valor_negocio": 0, "historias": [], "progreso_sprint": {},
        "impedimentos": [],
    }


def get_equipos(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "equipos.json", [])


def get_equipo(equipo_id: str, data_dir: str) -> dict:
    for e in get_equipos(data_dir):
        if e.get("id") == equipo_id:
            return e
    return {}


def get_catalogo_estimacion(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "catalogo_estimacion.json", {})


def get_policy(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "policy.json", {})
