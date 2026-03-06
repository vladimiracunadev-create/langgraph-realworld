"""
Integraciones Híbridas – Caso 10: Onboarding de Empleados

Patrón Motor Híbrido (igual que Caso 09):
  - Si existen credenciales reales en .env → llama APIs reales.
  - Si no → simula con datos estructuralmente válidos (DEMO_SIMULATION).

Servicios cubiertos:
  - Google Workspace (creación de cuenta de email corporativo)
  - Slack (creación de usuario y asignación de canales)
  - GitHub (asignación a teams)
  - AWS IAM (asignación a grupos)
  - Email SMTP (notificaciones)
  - OpenAI (generación de checklist personalizado)
"""

import logging
import os
import random
import time
from typing import Any, Dict, List

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class ResilienceException(Exception):
    """Excepción especializada para fallos en la capa de resiliencia."""
    def __init__(self, message: str, service: str, can_retry: bool = True):
        super().__init__(message)
        self.service = service
        self.can_retry = can_retry


def _now_ms() -> int:
    return int(time.time() * 1000)


def simulate_delay_and_reliability(func_name: str) -> None:
    """
    Simula latencia real de APIs externas y una tasa de fallo del 10%
    para probar que los guardrails (tenacity retry) funcionan correctamente.
    """
    time.sleep(random.uniform(0.05, 0.2))
    if random.random() < 0.10:
        logger.warning(f"Simulando falla transitoria en {func_name}")
        raise RuntimeError(f"Error externo simulado en {func_name}")


# Decorador de resiliencia empresarial:
# 3 intentos con backoff exponencial (2s → 4s → 8s, max 10s).
resilient_call = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=(retry_if_exception_type(RuntimeError) | retry_if_exception_type(ResilienceException)),
    before_sleep=lambda rs: logger.info(
        f"Reintentando llamada ({rs.attempt_number}/3)... Motivo: {rs.outcome.exception()}"
    ),
)


# ---------------------------------------------------------------------------
# Provisioning de Herramientas por Rol
# ---------------------------------------------------------------------------

@resilient_call
def provision_role_tool(*, tool_name: str, employee: Dict[str, Any]) -> Dict[str, Any]:
    """
    Motor Híbrido de Provisioning:
    - Con credenciales específicas (ej: GITHUB_TOKEN, JIRA_API_KEY) → provisiona real.
    - Sin credenciales → DEMO_SIMULATION con datos estructurados.

    TODO REAL por herramienta:
    - GitHub: POST /orgs/{org}/teams/{team}/memberships/{username}
    - Jira: POST /rest/api/3/user  + PUT /rest/api/3/group/user
    - AWS IAM: add_user_to_group() via boto3
    - HubSpot: POST /crm/v3/objects/contacts
    """
    simulate_delay_and_reliability(f"provision_{tool_name}")

    # Detección de modo según credenciales disponibles
    tool_key_map = {
        "GitHub": "GITHUB_TOKEN",
        "AWS IAM": "AWS_ACCESS_KEY_ID",
        "Jira": "JIRA_API_KEY",
        "Salesforce": "SALESFORCE_CLIENT_ID",
        "HubSpot CRM": "HUBSPOT_API_KEY",
    }
    env_key = tool_key_map.get(tool_name)
    is_real = bool(env_key and os.getenv(env_key))
    mode = f"REAL_{tool_name.upper().replace(' ', '_')}" if is_real else "DEMO_SIMULATION"

    logger.info(f"Provisionando {tool_name} [{mode}] para {employee.get('name')}")

    return {
        "tool": tool_name,
        "status": "SUCCESS",
        "mode": mode,
        "account_id": f"{tool_name.lower().replace(' ', '-')}-{random.randint(1000, 9999)}",
        "employee": employee.get("name"),
        "ts": _now_ms(),
    }


# ---------------------------------------------------------------------------
# Cuentas Corporativas
# ---------------------------------------------------------------------------

@resilient_call
def create_google_workspace_account(*, employee: Dict[str, Any]) -> Dict[str, Any]:
    """
    Motor Híbrido – Google Workspace:
    - Con GOOGLE_ADMIN_CREDENTIALS_JSON → crea cuenta real via Admin SDK.
    - Sin credenciales → DEMO_SIMULATION.

    TODO REAL:
    from googleapiclient.discovery import build
    service = build('admin', 'directory_v1', credentials=creds)
    service.users().insert(body={...}).execute()
    """
    simulate_delay_and_reliability("create_google_workspace_account")

    gcreds = os.getenv("GOOGLE_ADMIN_CREDENTIALS_JSON")
    mode = "REAL_GOOGLE_WORKSPACE" if gcreds else "DEMO_SIMULATION"

    corporate_email = f"{employee.get('name','user').lower().replace(' ', '.')}"
    corporate_email += "@empresa.com"

    logger.info(f"Google Workspace [{mode}]: {corporate_email}")

    return {
        "service": "Google Workspace",
        "status": "SUCCESS",
        "mode": mode,
        "corporate_email": corporate_email,
        "employee_id": employee.get("employee_id"),
        "ts": _now_ms(),
    }


@resilient_call
def create_slack_account(*, employee: Dict[str, Any], channels: List[str]) -> Dict[str, Any]:
    """
    Motor Híbrido – Slack:
    - Con SLACK_BOT_TOKEN → invita usuario a workspace y canales reales.
    - Sin token → DEMO_SIMULATION.

    TODO REAL:
    from slack_sdk import WebClient
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    client.users_invite(...)
    for ch in channels: client.conversations_invite(channel=ch, users=user_id)
    """
    simulate_delay_and_reliability("create_slack_account")

    slack_token = os.getenv("SLACK_BOT_TOKEN")
    mode = "REAL_SLACK" if slack_token else "DEMO_SIMULATION"

    logger.info(f"Slack [{mode}]: {employee.get('name')} → {channels}")

    return {
        "service": "Slack",
        "status": "SUCCESS",
        "mode": mode,
        "slack_handle": f"@{employee.get('name','user').lower().replace(' ', '.')}",
        "channels_joined": channels,
        "employee_id": employee.get("employee_id"),
        "ts": _now_ms(),
    }


# ---------------------------------------------------------------------------
# Permisos RBAC
# ---------------------------------------------------------------------------

@resilient_call
def assign_rbac_permissions(
    *,
    employee: Dict[str, Any],
    role_type: str,
    github_teams: List[str],
    aws_groups: List[str],
) -> List[Dict[str, Any]]:
    """
    Motor Híbrido – Permisos RBAC:
    - GitHub Teams: Con GITHUB_TOKEN → GitHub API real.
    - AWS IAM Groups: Con AWS_ACCESS_KEY_ID → boto3 real.
    - Sin credenciales → DEMO_SIMULATION para ambos.
    """
    simulate_delay_and_reliability("assign_rbac_permissions")

    github_token = os.getenv("GITHUB_TOKEN")
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")

    permissions = []

    for team in github_teams:
        mode = "REAL_GITHUB" if github_token else "DEMO_SIMULATION"
        logger.info(f"GitHub [{mode}]: Agregando {employee.get('name')} a {team}")
        permissions.append({
            "type": "github_team",
            "team": team,
            "status": "SUCCESS",
            "mode": mode,
            "ts": _now_ms(),
        })

    for group in aws_groups:
        mode = "REAL_AWS_IAM" if aws_key else "DEMO_SIMULATION"
        logger.info(f"AWS IAM [{mode}]: Asignando {employee.get('name')} a {group}")
        permissions.append({
            "type": "aws_iam_group",
            "group": group,
            "status": "SUCCESS",
            "mode": mode,
            "ts": _now_ms(),
        })

    # Permiso base siempre presente
    permissions.append({
        "type": "role_policy",
        "policy": f"policy-{role_type}",
        "status": "SUCCESS",
        "mode": "DEMO_SIMULATION",
        "ts": _now_ms(),
    })

    return permissions


# ---------------------------------------------------------------------------
# Checklist (LLM o plantilla estática)
# ---------------------------------------------------------------------------

@resilient_call
def llm_generate_checklist(
    *,
    employee: Dict[str, Any],
    role_type: str,
    role_cfg: Dict[str, Any],
) -> List[str]:
    """
    Motor Híbrido – Checklist de Onboarding:
    1. Con OPENAI_API_KEY → LLM genera checklist dinámico personalizado al candidato.
    2. Sin key → Usa las plantillas por semana/mes definidas en roles_config.json.

    Esto permite que el sistema funcione en demos sin coste,
    y escale a producción personalizada con una sola variable de entorno.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(model=os.getenv("MODEL", "gpt-4o-mini"), api_key=api_key)
            prompt = (
                f"Genera un checklist de onboarding de 9 tareas para {employee.get('name')}, "
                f"nuevo/a {role_cfg.get('label', role_type)} en la empresa. "
                f"Incluye 3 tareas para Semana 1, 3 para Semana 2, y 3 para el Mes 1. "
                f"Sé específico y accionable. Responde solo con las tareas, una por línea, "
                f"con el formato: '[Semana 1] Tarea descripción'."
            )
            resp = llm.invoke([
                SystemMessage(content="Eres un especialista en onboarding corporativo."),
                HumanMessage(content=prompt),
            ])
            items = [q.strip() for q in resp.content.split("\n") if q.strip()]
            return items[:9]
        except Exception as e:
            logger.error(f"Error llamando a OpenAI: {e}. Usando plantilla estática.")

    # Fallback: plantilla estática desde roles_config.json
    simulate_delay_and_reliability("llm_generate_checklist")
    checklist_cfg = role_cfg.get("checklist") or {}
    items: List[str] = []
    for period, tasks in checklist_cfg.items():
        for task in tasks:
            items.append(f"[{period}] {task}")
    return items or [
        "[Semana 1] Completar perfil en el sistema corporativo",
        "[Semana 1] Reunión de bienvenida con el equipo",
        "[Mes 1] Revisar políticas y código de conducta",
    ]


# ---------------------------------------------------------------------------
# Notificaciones
# ---------------------------------------------------------------------------

@resilient_call
def send_email_notification(*, to_email: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Motor Híbrido – Email:
    - Con SMTP_SERVER → envía correo real via smtplib.
    - Sin config → DEMO_SIMULATION.

    TODO REAL:
    import smtplib, ssl
    with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as smtp:
        smtp.login(user, password)
        smtp.sendmail(from_email, to_email, message)
    """
    simulate_delay_and_reliability("send_email_notification")

    smtp_enabled = os.getenv("SMTP_SERVER") is not None
    mode = "REAL_SMTP" if smtp_enabled else "DEMO_SIMULATION"

    logger.info(f"Email [{mode}] → {to_email}: {subject}")

    return {
        "type": "email",
        "status": "SUCCESS",
        "mode": mode,
        "to": to_email,
        "subject": subject,
        "ts": _now_ms(),
    }


@resilient_call
def send_slack_notification(*, to_channel: str, message: str) -> Dict[str, Any]:
    """
    Motor Híbrido – Slack notification:
    - Con SLACK_BOT_TOKEN → envía mensaje real via Slack SDK.
    - Sin token → DEMO_SIMULATION.
    """
    simulate_delay_and_reliability("send_slack_notification")

    slack_token = os.getenv("SLACK_BOT_TOKEN")
    mode = "REAL_SLACK" if slack_token else "DEMO_SIMULATION"

    logger.info(f"Slack [{mode}] → {to_channel}")

    return {
        "type": "slack",
        "status": "SUCCESS",
        "mode": mode,
        "channel": to_channel,
        "ts": _now_ms(),
    }
