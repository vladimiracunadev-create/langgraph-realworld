"""
integrations.py — Adaptadores de datos para Caso 21 (Documentación Automática).

DEMO: lectura local de repositorios.json, outline_template.json, quality_rules.json.
LIVE: en una integración real este módulo encapsularía clientes hacia
GitHub API, GitLab, Bitbucket, MkDocs build, Confluence REST y Notion API.
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


def get_repositorios(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "repositorios.json", [])


def get_repo(repo_id: str, data_dir: str) -> dict:
    repos = get_repositorios(data_dir)
    for r in repos:
        if r.get("id") == repo_id:
            return r
    if repos:
        logger.info("repo_id=%s no encontrado; fallback al primero.", repo_id)
        return repos[0]
    return {
        "id": repo_id, "nombre": "", "tipo": "api_rest", "lenguaje": "python",
        "modulos": [], "tests": {}, "changelog_entries": 0,
        "readme_existente": False, "ci_configurado": False,
    }


def get_outline_template(tipo: str, data_dir: str) -> list:
    template = _load_json(Path(data_dir) / "outline_template.json", {})
    return template.get(tipo, template.get("api_rest", {})).get("secciones", [])


def get_quality_rules(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "quality_rules.json", {})
