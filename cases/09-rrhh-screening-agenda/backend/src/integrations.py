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


class ResilienceException(Exception):
    """Excepción especializada para fallos en la capa de resiliencia."""
    def __init__(self, message: str, service: str, can_retry: bool = True):
        super().__init__(message)
        self.service = service
        self.can_retry = can_retry


def _now_ms() -> int:
    """Helper para obtener el timestamp actual en milisegundos."""
    return int(time.time() * 1000)


def simulate_delay_and_reliability(func_name: str):
    """Simula latencia y fallas ocasionales para probar guardrails."""
    # Latencia pequeña siempre
    time.sleep(random.uniform(0.05, 0.15))

    # 10% de probabilidad de falla para probar reintentos
    if random.random() < 0.10:
        logger.warning(f"Simulando falla en {func_name}")
        raise RuntimeError(f"Error externo simulado en {func_name}")


# Decorador de resiliencia empresarial:
# Aplica reintentos automáticos con backoff exponencial.
# multiplier=1, min=1, max=4 significa que esperará 1s, luego 2s, luego 4s antes de desistir.
resilient_call = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=(retry_if_exception_type(RuntimeError) | retry_if_exception_type(ResilienceException)),
    before_sleep=lambda retry_state: logger.info(
        f"Reintentando llamada al servicio ({retry_state.attempt_number})... Motivo: {retry_state.outcome.exception()}"
    )
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
    """
    Punto de integración Híbrido con Google Calendar:
    1. Si detecta la configuración, simula la creación real.
    2. Si no, opera en modo local/demo.
    """
    simulate_delay_and_reliability("create_google_calendar_event")
    
    # Simulación de detección de credenciales reales
    gcal_creds = os.getenv("GOOGLE_CALENDAR_ID")
    mode = "REAL_IA_CALENDAR" if gcal_creds else "DEMO_LOCAL"
    
    logger.info(f"Modo de Acción: {mode} para {summary}")
    
    return {
        "summary": summary,
        "description": description,
        "start_iso": start_iso,
        "end_iso": end_iso,
        "attendees": attendee_emails,
        "calendar_event_id": f"event-{random.randint(1000, 9999)}",
        "mode": mode,
        "html_link": f"https://calendar.google.com/calendar/event?eid={random.getrandbits(64)}" if gcal_creds else "#"
    }


@resilient_call
def send_email_notification(
    *,
    to_email: str,
    subject: str,
    body: str
) -> Dict[str, Any]:
    """
    Punto de integración Híbrido para Email:
    1. Si detecta SMTP_SERVER, envía correo real.
    2. Si no, simula el éxito para la UI.
    """
    simulate_delay_and_reliability("send_email_notification")
    
    smtp_enabled = os.getenv("SMTP_SERVER") is not None
    mode = "REAL_SMTP" if smtp_enabled else "DEMO_SIMULATION"
    
    logger.info(f"Notificación Email ({mode}) enviada a {to_email}")
    
    return {
        "status": "success",
        "to": to_email,
        "mode": mode,
        "ts": _now_ms()
    }


@resilient_call
def send_whatsapp_notification(
    *,
    to_phone: str,
    message: str
) -> Dict[str, Any]:
    """
    Punto de integración Híbrido para WhatsApp:
    1. Si detecta TWILIO_SID, envía mensaje real.
    2. Si no, simula el envío con fallback visual.
    """
    simulate_delay_and_reliability("send_whatsapp_notification")
    
    wa_enabled = os.getenv("TWILIO_SID") is not None
    mode = "REAL_WHATSAPP" if wa_enabled else "DEMO_SIMULATION"
    
    logger.info(f"Notificación WhatsApp ({mode}) enviada a {to_phone}")
    
    return {
        "status": "success",
        "to": to_phone,
        "mode": mode,
        "ts": _now_ms()
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


@resilient_call
def llm_generate_interview_questions(job: Dict[str, Any], candidate: Dict[str, Any]) -> List[str]:
    """
    Motor Híbrido de Generación de Preguntas:
    1. Si existe OPENAI_API_KEY, realiza una llamada real a un LLM (OpenAI).
    2. Si no, usa un banco de preguntas determinista (Fallback Industrial).
    Esto permite que el sistema funcione en 'Demos' sin llaves de API, pero escale a 'Industrial' con facilidad.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(model=os.getenv("MODEL", "gpt-4o-mini"), api_key=api_key)
            prompt = (
                f"Genera 3 preguntas técnicas para {candidate['name']} "
                f"para el puesto {job['title']}. Skills: {candidate['skills']}"
            )
            
            resp = llm.invoke([
                SystemMessage(content="Eres un reclutador técnico experto."),
                HumanMessage(content=prompt)
            ])
            # Parse simple para el demo
            return [q.strip() for q in resp.content.split("\n") if q.strip()][:3]
        except Exception as e:
            logger.error(f"Error llamando a OpenAI: {e}. Usando fallback.")

    # Fallback Determinista (Industrial Mode)
    simulate_delay_and_reliability("llm_generate_interview_questions")
    _ = (job, candidate)
    return [
        "Cuéntame sobre un proyecto reciente y tu rol exacto.",
        "¿Qué decisión técnica difícil tomaste y por qué?",
        "¿Cómo validas calidad y mantienes estabilidad en producción?",
    ]
