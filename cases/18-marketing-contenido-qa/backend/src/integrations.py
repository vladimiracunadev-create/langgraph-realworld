"""
integrations.py — Adaptadores de datos para Caso 18 (Marketing con QA).

DEMO: lectura local de briefs.json, brand_style.json, fact_sources.json, quality_rules.json.
LIVE: un cliente real envolvería CMS (HubSpot, Contentful), DAM, base de
conocimiento factual (Notion/Confluence) y APIs SEO (Semrush/Ahrefs).
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


def get_briefs(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "briefs.json", [])


def get_brief(brief_id: str, data_dir: str) -> dict:
    briefs = get_briefs(data_dir)
    for b in briefs:
        if b.get("id") == brief_id:
            return b
    if briefs:
        logger.info("brief_id=%s no encontrado; fallback al primero.", brief_id)
        return briefs[0]
    return {
        "id": brief_id, "titulo": "", "formato": "blog_post",
        "audiencia": "general", "tono": "profesional_cercano",
        "objetivo": "", "keywords": [],
        "hechos_obligatorios": [], "longitud_objetivo_palabras": 200,
    }


def get_brand_style(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "brand_style.json", {})


def get_fact_sources(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "fact_sources.json", {})


def get_quality_rules(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "quality_rules.json", {})
