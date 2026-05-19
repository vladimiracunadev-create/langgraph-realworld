"""
integrations.py — Adaptadores de datos para Caso 23 (Salud Pre-triage Administrativo).

DEMO: lectura local de sesiones.json, protocolo_urgencia.json, especialidades.json, policy.json.
LIVE: un cliente real envolvería HIS/HL7-FHIR, motor de protocolos clínicos validado,
sistema de agendamiento hospitalario y store auditable.
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


def get_sesiones(data_dir: str) -> list:
    return _load_json(Path(data_dir) / "sesiones.json", [])


def get_sesion(sesion_id: str, data_dir: str) -> dict:
    items = get_sesiones(data_dir)
    for s in items:
        if s.get("id") == sesion_id:
            return s
    if items:
        logger.info("sesion_id=%s no encontrada; fallback a la primera.", sesion_id)
        return items[0]
    return {
        "id": sesion_id, "canal": "desconocido",
        "paciente": {}, "motivo_consulta": "",
        "sintomas": [], "antecedentes": {},
    }


def get_protocolo(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "protocolo_urgencia.json", {})


def get_especialidades(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "especialidades.json", {})


def get_policy(data_dir: str) -> dict:
    return _load_json(Path(data_dir) / "policy.json", {})
