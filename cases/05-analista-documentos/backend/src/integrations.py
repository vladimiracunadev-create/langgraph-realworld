"""
integrations.py — Adaptadores de integración para Caso 05 (Analista de Documentos).

En modo DEMO todas las funciones operan sobre los archivos JSON locales
(documents.json, clause_patterns.json) sin dependencias externas.
En modo LIVE se habilitaría extracción real de PDFs/DOCX con PyMuPDF o
Amazon Textract, y clasificación semántica de cláusulas con embeddings.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _documents_path(data_dir: str) -> Path:
    return Path(data_dir) / "documents.json"


def _patterns_path(data_dir: str) -> Path:
    return Path(data_dir) / "clause_patterns.json"


def get_document(doc_id: str, data_dir: str) -> dict:
    """
    Lee documents.json y devuelve el documento con el id indicado.
    Si no existe, usa el primero como fallback DEMO.
    """
    path = _documents_path(data_dir)
    try:
        docs: list[dict] = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo leer documents.json: %s", exc)
        return {
            "id": doc_id,
            "title": "Documento DEMO",
            "type": "nda",
            "doc_format": "text",
            "parties": ["Parte A", "Parte B"],
            "date": "2026-01-01",
            "raw_text": (
                "CLÁUSULA 1: Confidencialidad\n"
                "Las partes se obligan a mantener confidencialidad e información confidencial.\n"
                "CLÁUSULA 2: Arbitraje\n"
                "Las controversias se resolverán por arbitraje ante la Cámara de Arbitraje Comercial."
            ),
        }

    for doc in docs:
        if doc.get("id") == doc_id:
            return doc

    logger.info("doc_id=%s no encontrado; usando el primero como fallback.", doc_id)
    return docs[0] if docs else {}


def get_clause_patterns(data_dir: str) -> dict:
    """
    Lee clause_patterns.json y devuelve el diccionario de patrones de cláusulas.
    En modo LIVE se complementaría con embeddings semánticos.
    """
    path = _patterns_path(data_dir)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo leer clause_patterns.json: %s", exc)
        return {
            "confidentiality": {
                "keywords": ["confidencialidad", "información confidencial"],
                "risk": "bajo",
                "description": "Obligaciones de confidencialidad",
                "checklist_item": "Confirmar alcance de confidencialidad",
                "escalation_reason": None,
            }
        }


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extrae texto de un PDF usando PyMuPDF (modo LIVE).
    Requiere: pip install pymupdf
    En modo DEMO no se invoca esta función.
    """
    try:
        import fitz  # PyMuPDF  # noqa: PLC0415
        doc = fitz.open(file_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        logger.info("LIVE: PDF extraído — %d caracteres desde %s", len(text), file_path)
        return text
    except ImportError:
        logger.warning("PyMuPDF no instalado; instala con: pip install pymupdf")
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Error extrayendo PDF %s: %s", file_path, exc)
        raise


def extract_text_from_docx(file_path: str) -> str:
    """
    Extrae texto de un DOCX usando python-docx (modo LIVE).
    Requiere: pip install python-docx
    En modo DEMO no se invoca esta función.
    """
    try:
        from docx import Document  # noqa: PLC0415
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        logger.info("LIVE: DOCX extraído — %d caracteres desde %s", len(text), file_path)
        return text
    except ImportError:
        logger.warning("python-docx no instalado; instala con: pip install python-docx")
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Error extrayendo DOCX %s: %s", file_path, exc)
        raise
