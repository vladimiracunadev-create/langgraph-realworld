"""
integrations.py — Capa de integraciones para Caso 19 - DevEx PR Review.

Soporta modo DEMO (sin credenciales reales) y modo LIVE (GitHub API real).
En modo DEMO todas las operaciones son stubs que loguean la acción.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DEMO_MODE = not os.getenv("GITHUB_TOKEN", "").strip()


def get_pr_data(pr_id: str, pr_data_path: str | None = None) -> dict:
    """
    Obtiene los datos del PR por ID.

    En modo DEMO: lee sample_pr.json desde pr_data_path o la ruta por defecto.
    En modo LIVE: consultaría la GitHub API real (no implementado aquí).

    Args:
        pr_id: Identificador del PR (ej. "PR-001").
        pr_data_path: Ruta al JSON del PR. Si es None, usa la var de entorno PR_DATA_PATH.

    Returns:
        dict con los datos del PR.
    """
    if DEMO_MODE:
        # Resolver la ruta del archivo de datos
        path = pr_data_path or os.getenv("PR_DATA_PATH", "")
        if not path:
            # Fallback: buscar relativo a la raíz del caso
            case_root = Path(__file__).resolve().parents[2]
            path = str(case_root / "data" / "sample_pr.json")

        logger.info(f"[DEMO] Cargando PR {pr_id} desde {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Si el JSON es un solo PR, devolverlo directamente
            if isinstance(data, dict):
                return data
            # Si es una lista, buscar por id
            if isinstance(data, list):
                for pr in data:
                    if pr.get("id") == pr_id:
                        return pr
                raise ValueError(f"PR {pr_id} no encontrado en {path}")
        except FileNotFoundError:
            logger.warning(f"[DEMO] Archivo no encontrado: {path}. Devolviendo PR simulado.")
            return _demo_pr_stub(pr_id)
    else:
        # Modo LIVE: aquí iría la llamada real a la GitHub API
        logger.info(f"[LIVE] Consultando GitHub API para PR {pr_id}")
        raise NotImplementedError("GitHub API integration not implemented. Set GITHUB_TOKEN to enable.")


def post_review_comment(pr_id: str, comment: str) -> dict:
    """
    Publica un comentario de revisión en el PR.

    En modo DEMO: loguea el comentario sin hacer ninguna llamada externa.
    En modo LIVE: publicaría el comentario vía GitHub API.

    Args:
        pr_id: Identificador del PR.
        comment: Texto del comentario de revisión.

    Returns:
        dict con el resultado de la operación.
    """
    if DEMO_MODE:
        logger.info(f"[DEMO] Comentario en PR {pr_id}: {comment[:120]}{'...' if len(comment) > 120 else ''}")
        return {"mode": "DEMO", "pr_id": pr_id, "status": "comment_logged", "comment_preview": comment[:80]}
    else:
        logger.info(f"[LIVE] Publicando comentario en PR {pr_id}")
        raise NotImplementedError("GitHub API integration not implemented.")


def approve_pr(pr_id: str) -> dict:
    """
    Aprueba el PR.

    En modo DEMO: loguea la aprobación sin hacer ninguna llamada externa.
    En modo LIVE: aprobaría el PR vía GitHub Review API.

    Args:
        pr_id: Identificador del PR.

    Returns:
        dict con el resultado de la operación.
    """
    if DEMO_MODE:
        logger.info(f"[DEMO] PR {pr_id} aprobado (stub).")
        return {"mode": "DEMO", "pr_id": pr_id, "status": "approved"}
    else:
        logger.info(f"[LIVE] Aprobando PR {pr_id}")
        raise NotImplementedError("GitHub API integration not implemented.")


def request_changes(pr_id: str, reasons: list[str]) -> dict:
    """
    Solicita cambios en el PR.

    En modo DEMO: loguea los motivos sin hacer ninguna llamada externa.
    En modo LIVE: solicitaría cambios vía GitHub Review API.

    Args:
        pr_id: Identificador del PR.
        reasons: Lista de razones por las que se solicitan cambios.

    Returns:
        dict con el resultado de la operación.
    """
    if DEMO_MODE:
        logger.info(f"[DEMO] Solicitud de cambios en PR {pr_id}. Motivos: {len(reasons)} finding(s).")
        for i, reason in enumerate(reasons, 1):
            logger.info(f"  [{i}] {reason}")
        return {
            "mode": "DEMO",
            "pr_id": pr_id,
            "status": "changes_requested",
            "reasons_count": len(reasons),
        }
    else:
        logger.info(f"[LIVE] Solicitando cambios en PR {pr_id}")
        raise NotImplementedError("GitHub API integration not implemented.")


def _demo_pr_stub(pr_id: str) -> dict:
    """PR simulado de fallback cuando no existe el archivo de datos."""
    return {
        "id": pr_id,
        "title": "feat: demo PR (fallback stub)",
        "author": "demo-user",
        "base_branch": "main",
        "head_branch": "feat/demo",
        "diff": (  # noqa: E501
            "diff --git a/app.py b/app.py\n+def search(q):\n"
            "+    sql = 'SELECT * FROM t WHERE name=' + q\n"
            "+    cursor.execute(sql)"
        ),
        "files_changed": ["app.py"],
        "commits": ["feat: add demo feature"],
    }
