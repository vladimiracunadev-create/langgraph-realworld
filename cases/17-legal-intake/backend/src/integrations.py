"""
integrations.py — Adaptadores de datos para Caso 17 (Legal Intake).

En modo DEMO opera sobre archivos JSON locales:
  intakes.json, specialty_keywords.json, required_fields.json,
  templates.json, lawyers.json
En modo LIVE el LLM puede complementar la clasificación y la redacción
del borrador del documento.
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


def get_intake(intake_id: str, data_dir: str) -> dict:
    path = Path(data_dir) / "intakes.json"
    intakes = _load_json(path, [])
    for it in intakes:
        if it.get("id") == intake_id:
            return it
    if intakes:
        logger.info("intake_id=%s no encontrado; fallback al primero.", intake_id)
        return intakes[0]
    return {
        "id": intake_id,
        "cliente_nombre": "Cliente DEMO",
        "cliente_contacto": "demo@ejemplo.cl",
        "fecha_solicitud": "2026-01-01",
        "asunto_libre": "Consulta legal genérica.",
        "documentos_aportados": [],
    }


def get_specialty_keywords(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "specialty_keywords.json", {})


def get_required_fields(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "required_fields.json", {})


def get_templates(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "templates.json", {})


def get_lawyers(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "lawyers.json", [])


def render_template(template: str, variables: dict) -> str:
    """
    Sustitución simple {{key}} → valor. Mantiene los placeholders no resueltos
    para que el abogado revisor los identifique como pendientes.
    """
    out = template
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        if placeholder in out:
            out = out.replace(placeholder, str(value) if value else "{{PENDIENTE: " + key + "}}")
    return out
