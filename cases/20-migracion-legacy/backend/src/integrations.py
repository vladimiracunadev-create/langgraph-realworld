"""
integrations.py — Adaptadores de datos para Caso 20 (Migración Legacy).

DEMO: lectura local de proyectos.json, dependencias.json, lotes_catalog.json, policy.json.
LIVE: un cliente real envolvería repos Git, parsers tree-sitter, runners pytest/junit/jest,
bases de conocimiento de regresión y un store append-only para el plan de migración.
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


def get_proyectos(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "proyectos.json", [])


def get_proyecto(proyecto_id: str, data_dir: str) -> dict:
    items = get_proyectos(data_dir)
    for p in items:
        if p.get("id") == proyecto_id:
            return p
    if items:
        logger.info("proyecto_id=%s no encontrado; fallback al primero.", proyecto_id)
        return items[0]
    return {
        "id": proyecto_id,
        "nombre": "desconocido",
        "lenguaje_origen": "",
        "lenguaje_destino": "",
        "modulos": [],
        "loc_total": 0,
        "complejidad_promedio": 0,
        "deuda_tecnica_score": 0,
        "descripcion": "",
    }


def get_dependencias(proyecto_id: str, data_dir: str) -> dict:
    todo = _load_json(Path(data_dir) / "dependencias.json", {})
    return todo.get(proyecto_id, {})


def get_lotes_catalog(proyecto_id: str, data_dir: str) -> dict:
    todo = _load_json(Path(data_dir) / "lotes_catalog.json", {})
    return todo.get(proyecto_id, {})


def get_policy(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "policy.json", {})
