"""Integraciones "reales" (stubs + guías)

Este módulo NO implementa la integración final (eso lo harás tú),
pero deja:
- librerías instaladas (requirements.txt)
- funciones stub
- comentarios precisos de cómo conectarlo.

Objetivo: que cuando decidas hacer el flujo real, sepas EXACTAMENTE
dónde tocar y qué credenciales necesitas.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List


# ----------------------------
# 1) Parsing de CV / documentos
# ----------------------------

def parse_resume_to_text(file_path: str) -> str:
    """Convierte un CV (PDF/DOCX/TXT) a texto plano.

    Implementación real sugerida:
    - Si es PDF: usa `pypdf` primero (rápido) y si falla, `pdfminer.six` (más robusto).
    - Si es DOCX: usa `python-docx`.
    - Guarda el texto crudo en DB (para auditoría) y también una versión normalizada (para scoring).
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    # TODO REAL: implementar PDF/DOCX
    # Ejemplo PDF rápido:
    #   from pypdf import PdfReader
    #   reader = PdfReader(file_path)
    #   text = "\n".join(page.extract_text() or "" for page in reader.pages)
    #   return text
    #
    # Ejemplo DOCX:
    #   import docx
    #   d = docx.Document(file_path)
    #   return "\n".join(p.text for p in d.paragraphs)

    return ""


def extract_candidate_signals(text: str) -> Dict[str, Any]:
    """Extrae señales del CV: skills, años de experiencia, links, etc.

    TODO REAL:
    - Usar reglas + LLM (o ambos):
      - regex / diccionarios de skills
      - extracción de años (ranges, fechas)
      - linkedin/github/url
    - Persistir señales en DB
    """
    _ = text
    return {
        "skills": [],
        "years_experience": 0,
        "portfolio_url": "",
        "soft_skills": [],
    }


# ----------------------------
# 2) Persistencia / DB / ATS
# ----------------------------

def upsert_candidate_in_db(candidate: Dict[str, Any]) -> None:
    """Inserta/actualiza candidato en DB.

    TODO REAL:
    - conectar a Postgres/MySQL/SQL Server
    - upsert por candidate_id/email
    """
    _ = candidate
    return


def update_ats_status(candidate_id: str, status: str) -> None:
    """Actualiza el estado del candidato en un ATS (Lever/Greenhouse/etc).

    TODO REAL:
    - API del ATS
    - registrar auditoría
    """
    _ = candidate_id
    _ = status
    return


# ----------------------------
# 3) Google Calendar (stub)
# ----------------------------

def create_google_calendar_event(
    *,
    summary: str,
    description: str,
    start_iso: str,
    end_iso: str,
    attendee_emails: List[str],
) -> Dict[str, Any]:
    """Crea un evento de Google Calendar.

    TODO REAL (recomendado):
    - google-api-python-client
    - OAuth2 / Service Account (según escenario)
    - manejar timezones correctamente
    """
    return {
        "summary": summary,
        "description": description,
        "start_iso": start_iso,
        "end_iso": end_iso,
        "attendees": attendee_emails,
        "calendar_event_id": "stub-event",
    }


# ----------------------------
# 4) Envío de correo (SMTP / SendGrid)
# ----------------------------

async def send_email_smtp_async(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    use_tls: bool,
    from_email: str,
    to_email: str,
    subject: str,
    body_text: str,
) -> None:
    """Envía correo por SMTP (async).

    TODO REAL:
    - aiosmtplib
    - email.message.EmailMessage
    - starttls según config
    """
    _ = (
        host,
        port,
        username,
        password,
        use_tls,
        from_email,
        to_email,
        subject,
        body_text,
    )
    return


def send_email_sendgrid(
    *,
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    body_text: str,
) -> None:
    """Envía correo con SendGrid.

    TODO REAL:
    - sendgrid
    - manejar errores/retornos y auditoría
    """
    _ = (api_key, from_email, to_email, subject, body_text)
    return


# ----------------------------
# 5) LLM (stub)
# ----------------------------

def llm_generate_interview_questions(job: Dict[str, Any], candidate: Dict[str, Any]) -> List[str]:
    """Genera preguntas de entrevista.

    TODO REAL:
    - Integrar OpenAI / Azure OpenAI / local LLM
    - Guardar prompt+respuesta para auditoría
    """
    _ = (job, candidate)
    return [
        "Cuéntame sobre un proyecto reciente y tu rol exacto.",
        "¿Qué decisión técnica difícil tomaste y por qué?",
        "¿Cómo validas calidad y mantienes estabilidad en producción?",
    ]
