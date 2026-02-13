"""Integraciones "reales" (stubs + guías)

Este módulo NO implementa la integración final (eso lo harás tú),
pero deja:
- funciones stub
- comentarios precisos de cómo conectarlo
"""

import logging
import os
import random
import time
from typing import Any, Dict, List

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

# Configuración básica de logging
logger = logging.getLogger(__name__)


def simulate_delay_and_reliability(func_name: str):
    """Simula latencia y fallas ocasionales para probar guardrails."""
    # Latencia pequeña siempre
    time.sleep(random.uniform(0.05, 0.15))

    # 10% de probabilidad de falla para probar reintentos
    if random.random() < 0.10:
        logger.warning(f"Simulando falla en {func_name}")
        raise RuntimeError(f"Error externo simulado en {func_name}")


# Decorador de resiliencia real
resilient_call = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type(RuntimeError),
    before_sleep=lambda retry_state: logger.info(f"Reintentando llamada ({retry_state.attempt_number})...")
)


@resilient_call
def parse_resume_to_text(file_path: str) -> str:
    """Convierte un CV (PDF/DOCX/TXT) a texto plano (con reintentos)."""
    simulate_delay_and_reliability("parse_resume_to_text")
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


@resilient_call
def create_google_calendar_event(
    *,
    summary: str,
    description: str,
    start_iso: str,
    end_iso: str,
    attendee_emails: List[str],
) -> Dict[str, Any]:
    """Crea un evento de Google Calendar (con reintentos)."""
    simulate_delay_and_reliability("create_google_calendar_event")
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


@resilient_call
def llm_generate_interview_questions(job: Dict[str, Any], candidate: Dict[str, Any]) -> List[str]:
    """Genera preguntas de entrevista (con reintentos)."""
    simulate_delay_and_reliability("llm_generate_interview_questions")
    _ = (job, candidate)
    return [
        "Cuéntame sobre un proyecto reciente y tu rol exacto.",
        "¿Qué decisión técnica difícil tomaste y por qué?",
        "¿Cómo validas calidad y mantienes estabilidad en producción?",
    ]
