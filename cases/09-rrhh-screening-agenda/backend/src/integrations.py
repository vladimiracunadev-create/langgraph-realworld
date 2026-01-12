"""Integraciones "reales" (stubs + guías)

Este módulo NO implementa la integración final (eso lo harás tú),
pero deja:
- librerías instaladas (requirements.txt)
- funciones stub
- comentarios precisos de cómo conectarlo.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List


def parse_resume_to_text(file_path: str) -> str:
    """Convierte un CV (PDF/DOCX/TXT) a texto plano (stub)."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    # TODO REAL: implementar PDF/DOCX con pypdf/pdfminer.six y python-docx.
    return ""


def extract_candidate_signals(text: str) -> Dict[str, Any]:
    """Extrae señales del CV: skills, años de experiencia, links, etc (stub)."""
    _ = text
    return {
        "skills": [],
        "years_experience": 0,
        "portfolio_url": "",
        "soft_skills": [],
    }


def upsert_candidate_in_db(candidate: Dict[str, Any]) -> None:
    """Inserta/actualiza candidato en DB (stub)."""
    _ = candidate
    return


def update_ats_status(candidate_id: str, status: str) -> None:
    """Actualiza estado del candidato en un ATS (stub)."""
    _ = candidate_id
    _ = status
    return


def create_google_calendar_event(
    *,
    summary: str,
    description: str,
    start_iso: str,
    end_iso: str,
    attendee_emails: List[str],
) -> Dict[str, Any]:
    """Crea un evento de Google Calendar (stub)."""
    return {
        "summary": summary,
        "description": description,
        "start_iso": start_iso,
        "end_iso": end_iso,
        "attendees": attendee_emails,
        "calendar_event_id": "stub-event",
    }


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
    """Envía correo por SMTP (async) (stub)."""
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
    """Envía correo con SendGrid (stub)."""
    _ = (api_key, from_email, to_email, subject, body_text)
    return


def llm_generate_interview_questions(job: Dict[str, Any], candidate: Dict[str, Any]) -> List[str]:
    """Genera preguntas de entrevista (stub)."""
    _ = (job, candidate)
    return [
        "Cuéntame sobre un proyecto reciente y tu rol exacto.",
        "¿Qué decisión técnica difícil tomaste y por qué?",
        "¿Cómo validas calidad y mantienes estabilidad en producción?",
    ]
