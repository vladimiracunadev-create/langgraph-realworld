"""
integrations.py — Adaptadores de datos para Caso 11 (Tutor Adaptativo).

DEMO: lectura local de students.json, item_bank.json y tutor_policy.json.
LIVE: en una integración real este módulo encapsularía clientes de LMS
(Moodle, Canvas, Google Classroom), bases vectoriales de contenidos
(pgvector), y servicios de evaluación con LLM para respuestas abiertas.
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


def get_student(student_id: str, data_dir: str) -> dict:
    students = _load_json(Path(data_dir) / "students.json", [])
    for s in students:
        if s.get("id") == student_id:
            return s
    if students:
        logger.info("student_id=%s no encontrado; fallback al primero.", student_id)
        return students[0]
    return {
        "id": student_id,
        "nombre": "",
        "curso": "",
        "dominio": "",
        "habilidad_inicial": None,
        "objetivo_sesion": "",
        "preferencia_formato": "explicacion",
        "intentos_max_por_concepto": 2,
        "seed": 0,
    }


def get_item_bank(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "item_bank.json", [])


def get_policy(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "tutor_policy.json", {})
