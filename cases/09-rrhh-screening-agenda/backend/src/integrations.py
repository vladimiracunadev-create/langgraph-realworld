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
import re

# ----------------------------
# 1) Parsing de CV / documentos
# ----------------------------

def parse_resume_to_text(file_path: str) -> str:
    """Convierte un CV (PDF/DOCX/TXT) a texto plano.

    Implementación real sugerida:
    - Si es PDF: usa `pypdf` primero (rápido) y si falla, `pdfminer.six` (más robusto).
    - Si es DOCX: usa `python-docx`.
    - Guarda el texto crudo en DB (para auditoría) y también una versión normalizada (para scoring).

    Requisitos:
    - pypdf
    - pdfminer.six
    - python-docx
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        # TODO REAL:
        # from pypdf import PdfReader
        # reader = PdfReader(file_path)
        # text = "\n".join(page.extract_text() or "" for page in reader.pages)
        # if not text.strip(): fallback pdfminer
        return ""  # placeholder

    if ext == ".docx":
        # TODO REAL:
        # import docx
        # doc = docx.Document(file_path)
        # text = "\n".join(p.text for p in doc.paragraphs)
        return ""  # placeholder

    if ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    # TODO REAL: soportar .doc (legacy) vía conversión externa (LibreOffice headless) si lo necesitas
    return ""


def extract_candidate_signals(text: str) -> Dict[str, Any]:
    """Extrae señales desde el texto del CV: skills, años, educación, links.

    Implementación real sugerida:
    - Skills:
        - Diccionario controlado (lista de skills que te importan) + fuzzy matching (rapidfuzz)
        - O embeddings/LLM para extracción semántica
    - Años de experiencia:
        - heurística (regex: 'X años', fechas) + dateparser
    - Links:
        - regex para GitHub/LinkedIn/portafolio
    """
    # TODO REAL: reemplaza por extracción real.
    return {
        "skills": [],
        "years_experience": 0,
        "education": "",
        "portfolio_url": "",
        "linkedin_url": "",
        "email": "",
        "phone": "",
    }


# ----------------------------
# 2) Persistencia / ATS / DB
# ----------------------------

def upsert_candidate_in_db(candidate: Dict[str, Any]) -> None:
    """Guarda/actualiza candidato en una base real.

    Opciones:
    - SQLite (rápido) -> luego Postgres (producción)
    - ORM: SQLAlchemy (no lo incluí para mantenerlo simple, pero puedes agregarlo)

    Campos sugeridos:
    - candidate_id, nombre, email, teléfono
    - raw_resume_text, normalized_resume_text
    - extracted_signals (json)
    - score, status, timestamps
    """
    # TODO REAL: implementar con tu DB/ORM
    return


def update_ats_status(candidate_id: str, status: str) -> None:
    """Actualiza estado en ATS (Greenhouse/Lever/etc).

    Implementación real sugerida:
    - Consumir API REST del ATS con httpx
    - Guardar request/response (auditoría)
    - Reintentos con tenacity
    """
    # TODO REAL
    return


# ----------------------------
# 3) Calendar (Google) / scheduling
# ----------------------------

def create_google_calendar_event(
    *,
    summary: str,
    description: str,
    start_iso: str,
    end_iso: str,
    attendee_emails: List[str],
    calendar_id: str = "primary",
) -> Dict[str, Any]:
    """Crea un evento real en Google Calendar.

    Requisitos:
    - google-api-python-client
    - google-auth
    - google-auth-oauthlib
    - google-auth-httplib2

    Setup real (alto nivel):
    1) Crear un proyecto en Google Cloud Console
    2) Habilitar Google Calendar API
    3) Crear credenciales OAuth2 (Desktop/Web)
    4) Guardar `credentials.json` en un lugar seguro (NO en git)
    5) En primera ejecución se genera `token.json` (refresh token)

    Referencia de implementación:
    - googleapiclient.discovery.build("calendar", "v3", credentials=creds)
    - service.events().insert(calendarId=calendar_id, body=event).execute()

    Aquí solo dejamos stub.
    """
    # TODO REAL: implementar OAuth2 + insertar evento
    return {"ok": False, "reason": "stub"}


# ----------------------------
# 4) Email / Notificaciones
# ----------------------------

def send_email_smtp_async(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    to_email: str,
    subject: str,
    body_text: str,
    use_tls: bool = True,
) -> None:
    """Envía correo real vía SMTP (async).

    Requisito:
    - aiosmtplib

    Notas:
    - En producción, ideal usar proveedor (SendGrid/Mailgun/AWS SES) por entregabilidad.
    """
    # TODO REAL:
    # import aiosmtplib
    # from email.message import EmailMessage
    # msg = EmailMessage()
    # msg["From"] = username
    # msg["To"] = to_email
    # msg["Subject"] = subject
    # msg.set_content(body_text)
    # await aiosmtplib.send(msg, hostname=host, port=port, username=username, password=password, start_tls=use_tls)
    return


def send_email_sendgrid(
    *,
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    body_text: str,
) -> None:
    """Envía correo real vía SendGrid API.

    Requisito:
    - sendgrid

    Setup real:
    - Crear API key en SendGrid
    - Guardarla en env var `SENDGRID_API_KEY`
    """
    # TODO REAL:
    # from sendgrid import SendGridAPIClient
    # from sendgrid.helpers.mail import Mail
    # message = Mail(from_email=from_email, to_emails=to_email, subject=subject, plain_text_content=body_text)
    # sg = SendGridAPIClient(api_key)
    # sg.send(message)
    return


# ----------------------------
# 5) LLM (opcional) para hacerlo "más real"
# ----------------------------

def llm_generate_interview_questions(candidate: Dict[str, Any], job: Dict[str, Any]) -> List[str]:
    """Genera preguntas de entrevista con un LLM (opcional).

    Requisitos:
    - openai
    - langchain-openai (si quieres integrar con LC)
    - O cualquier proveedor compatible

    Buenas prácticas:
    - Forzar formato de salida (JSON) con esquema
    - Guardar prompts + outputs (auditoría)
    - Poner límites y filtros (compliance)
    """
    # TODO REAL: implementar llamada al modelo y devolver lista de preguntas
    return []
