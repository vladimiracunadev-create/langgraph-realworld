"""
Caso 10 – Onboarding de Empleados
LangGraph StateGraph: flujo de ramificación condicional por rol.

Fases:
  1. load_employee       → Carga perfil + config de roles
  2. classify_role       → Detecta tipo de empleado
  3. provision_tools     → Provisiona herramientas del rol (hybrid mock/real)
  4. create_accounts     → Crea cuentas corporativas comunes
  5. assign_permissions  → Aplica permisos RBAC
  6. generate_checklist  → Genera checklist personalizado (LLM o plantilla)
  7. send_welcome        → Envía email + Slack al manager
  8. confirm_onboarding  → Marca completo, emite resumen
"""

import json
import logging
import operator
import os
import sqlite3
import time
from pathlib import Path
from typing import Annotated, Any, Dict, List

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from .settings import data_dir, load_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Estado del Agente (Single Source of Truth)
# ---------------------------------------------------------------------------

class OnboardingState(TypedDict, total=False):
    """
    Estado centralizado del flujo de onboarding.
    Cambiado a TypedDict para compatibilidad nativa con diccionarios.
    """
    employee: Dict[str, Any]
    roles_config: Dict[str, Any]
    role_type: str
    tools_provisioned: List[Dict[str, Any]]
    accounts: List[Dict[str, Any]]
    permissions: List[Dict[str, Any]]
    checklist: List[str]
    notifications: List[Dict[str, Any]]
    events: Annotated[List[Dict[str, Any]], operator.add]
    done: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_ms() -> int:
    return int(time.time() * 1000)


def _push_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Genera un delta de estado con un nuevo evento de auditoría."""
    return {
        "events": [{"ts": _now_ms(), "type": event_type, "data": data}]
    }


# ---------------------------------------------------------------------------
# Nodos del Grafo
# ---------------------------------------------------------------------------

def load_employee(state: OnboardingState) -> Dict[str, Any]:
    """
    Nodo 1 – Lectura:
    Carga el perfil del empleado (employee.json) y la configuración
    de herramientas por rol (roles_config.json) desde el directorio de datos.
    En producción esto consultaría un HRIS (ej: Workday, BambooHR).
    """
    logger.info("Cargando perfil del nuevo empleado...")
    load_settings()
    dd = data_dir()

    with open(os.path.join(dd, "employee.json"), "r", encoding="utf-8") as f:
        employee = json.load(f)
    with open(os.path.join(dd, "roles_config.json"), "r", encoding="utf-8") as f:
        roles_config = json.load(f)

    out: Dict[str, Any] = {
        "employee": employee,
        "roles_config": roles_config,
        "events": state.get("events", []) or [],
    }
    out.update(_push_event("loaded", {
        "employee_id": employee.get("employee_id"),
        "name": employee.get("name"),
        "role": employee.get("role"),
        "start_date": employee.get("start_date"),
    }))
    return out


def classify_role(state: OnboardingState) -> Dict[str, Any]:
    """
    Nodo 2 – Clasificación:
    Determina la categoría de rol del empleado para adaptar
    el flujo de provisioning. Si el rol es desconocido, cae a 'ops'
    como degradación graciosa.
    """
    employee = state.get("employee") or {}
    role = (employee.get("role") or "ops").lower()

    valid_roles = {"dev_backend", "dev_frontend", "sales", "ops", "mgmt"}
    role_type = role if role in valid_roles else "ops"

    logger.info(f"Rol clasificado: '{role_type}' para {employee.get('name')}")

    out: Dict[str, Any] = {"role_type": role_type}
    out.update(_push_event("classified", {
        "role_type": role_type,
        "employee": employee.get("name"),
        "department": employee.get("department"),
    }))
    return out


def provision_tools(state: OnboardingState) -> Dict[str, Any]:
    """
    Nodo 3 – Provisioning de Herramientas:
    Configura las herramientas específicas del rol (GitHub, Jira, Salesforce...).
    Usa el motor híbrido de integrations.py:
    - Con credenciales reales: llama APIs reales.
    - Sin credenciales: simula con DEMO_SIMULATION.
    Resiliencia: si una herramienta falla, continúa con las demás (degradación graciosa).
    """
    from .integrations import provision_role_tool

    role_type = state.get("role_type") or "ops"
    roles_config = state.get("roles_config") or {}
    employee = state.get("employee") or {}

    role_cfg = roles_config.get(role_type) or {}
    tools = role_cfg.get("tools") or []

    provisioned: List[Dict[str, Any]] = []
    for tool_name in tools:
        try:
            result = provision_role_tool(tool_name=tool_name, employee=employee)
            provisioned.append(result)
        except Exception as e:
            logger.error(f"Error provisionando {tool_name}: {e}")
            provisioned.append({
                "tool": tool_name,
                "status": "FAILED_DEGRADED",
                "mode": "ERROR",
                "error": str(e),
            })

    out: Dict[str, Any] = {"tools_provisioned": provisioned}
    out.update(_push_event("tools_provisioned", {
        "count": len(provisioned),
        "role": role_type,
        "tools": [t.get("tool") for t in provisioned],
    }))
    return out


def create_corporate_accounts(state: OnboardingState) -> Dict[str, Any]:
    """
    Nodo 4 – Cuentas Corporativas:
    Crea las cuentas comunes para todos los empleados independientemente del rol:
    Google Workspace (email corporativo) y Slack (con los canales del rol).
    Cada servicio falla en forma aislada (try/except por servicio).
    """
    from .integrations import create_google_workspace_account, create_slack_account

    employee = state.get("employee") or {}
    roles_config = state.get("roles_config") or {}
    role_type = state.get("role_type") or "ops"
    slack_channels = (roles_config.get(role_type) or {}).get("slack_channels") or []

    accounts: List[Dict[str, Any]] = []

    # Google Workspace
    try:
        gw = create_google_workspace_account(employee=employee)
        accounts.append(gw)
    except Exception as e:
        logger.error(f"Error creando Google Workspace: {e}")
        accounts.append({"service": "Google Workspace", "status": "FAILED_DEGRADED", "error": str(e)})

    # Slack
    try:
        slack = create_slack_account(employee=employee, channels=slack_channels)
        accounts.append(slack)
    except Exception as e:
        logger.error(f"Error creando cuenta Slack: {e}")
        accounts.append({"service": "Slack", "status": "FAILED_DEGRADED", "error": str(e)})

    out: Dict[str, Any] = {"accounts": accounts}
    out.update(_push_event("accounts_created", {
        "count": len(accounts),
        "services": [a.get("service") for a in accounts],
    }))
    return out


def assign_permissions(state: OnboardingState) -> Dict[str, Any]:
    """
    Nodo 5 – Permisos RBAC:
    Asigna permisos en GitHub (teams) y AWS (grupos IAM) según el rol.
    En producción esto llamaría a la API de GitHub y AWS IAM/SSO.
    """
    from .integrations import assign_rbac_permissions

    employee = state.get("employee") or {}
    role_type = state.get("role_type") or "ops"
    roles_config = state.get("roles_config") or {}
    role_cfg = roles_config.get(role_type) or {}

    try:
        permissions = assign_rbac_permissions(
            employee=employee,
            role_type=role_type,
            github_teams=role_cfg.get("github_teams") or [],
            aws_groups=role_cfg.get("aws_groups") or [],
        )
    except Exception as e:
        logger.error(f"Error asignando permisos RBAC: {e}")
        permissions = [{"type": "rbac", "status": "FAILED_DEGRADED", "role": role_type, "error": str(e)}]

    out: Dict[str, Any] = {"permissions": permissions}
    out.update(_push_event("permissions_assigned", {
        "role": role_type,
        "count": len(permissions),
    }))
    return out


def generate_checklist(state: OnboardingState) -> Dict[str, Any]:
    """
    Nodo 6 – Checklist Personalizado:
    Motor Híbrido:
    - Con OPENAI_API_KEY: el LLM genera un checklist dinámico adaptado al candidato.
    - Sin key: usa la plantilla estática definida en roles_config.json.
    """
    from .integrations import llm_generate_checklist

    employee = state.get("employee") or {}
    role_type = state.get("role_type") or "ops"
    roles_config = state.get("roles_config") or {}

    try:
        checklist = llm_generate_checklist(
            employee=employee,
            role_type=role_type,
            role_cfg=roles_config.get(role_type) or {},
        )
    except Exception as e:
        logger.error(f"Error generando checklist: {e}")
        checklist = [
            "Completar perfil en sistema corporativo",
            "Reunión de bienvenida con el team",
            "Revisar políticas y código de conducta",
        ]

    out: Dict[str, Any] = {"checklist": checklist}
    out.update(_push_event("checklist_generated", {
        "count": len(checklist),
        "role": role_type,
        "mode": "LLM" if os.getenv("OPENAI_API_KEY") else "STATIC_TEMPLATE",
    }))
    return out


def send_welcome_package(state: OnboardingState) -> Dict[str, Any]:
    """
    Nodo 7 – Bienvenida:
    Envía dos notificaciones en forma aislada (fallos no bloquean al otro):
    1. Email de bienvenida al nuevo empleado (con accesos y checklist).
    2. Mensaje de Slack al manager para notificar que el onboarding está listo.
    Motor híbrido: REAL_SMTP / REAL_SLACK o DEMO_SIMULATION según .env.
    """
    from .integrations import send_email_notification, send_slack_notification

    employee = state.get("employee") or {}
    checklist = state.get("checklist") or []
    accounts = state.get("accounts") or []
    role_type = state.get("role_type") or "ops"

    notifications: List[Dict[str, Any]] = []

    # 1. Email al nuevo empleado
    try:
        services = ", ".join([a.get("service", "") for a in accounts if a.get("status") != "FAILED_DEGRADED"])
        preview = " | ".join(checklist[:3])
        email_res = send_email_notification(
            to_email=employee.get("email", "nuevo@empresa.com"),
            subject=f"¡Bienvenido/a a bordo, {employee.get('name')}! 🚀",
            body=(
                f"Hola {employee.get('name')}, tu inicio es el {employee.get('start_date')}.\n"
                f"Tus cuentas listas: {services}.\n"
                f"Primeros pasos: {preview}..."
            ),
        )
        notifications.append({**email_res, "recipient": "employee"})
    except Exception as e:
        logger.error(f"Falla crítica en email al empleado: {e}")
        notifications.append({"type": "email", "status": "FAILED_DEGRADED", "recipient": "employee"})

    # 2. Slack al manager
    try:
        slack_res = send_slack_notification(
            to_channel=employee.get("manager_slack", "#management"),
            message=(
                f"✅ Onboarding completado para *{employee.get('name')}* "
                f"({role_type}). Accesos y checklist listos."
            ),
        )
        notifications.append({**slack_res, "recipient": "manager"})
    except Exception as e:
        logger.error(f"Falla crítica en Slack al manager: {e}")
        notifications.append({"type": "slack", "status": "FAILED_DEGRADED", "recipient": "manager"})

    out: Dict[str, Any] = {"notifications": notifications}
    out.update(_push_event("welcome_sent", {
        "count": len(notifications),
        "employee": employee.get("name"),
    }))
    return out


def confirm_onboarding(state: OnboardingState) -> Dict[str, Any]:
    """
    Nodo 8 – Confirmación Final:
    Marca el proceso como completo y emite un evento de resumen
    con todos los contadores del onboarding para el dashboard.
    """
    employee = state.get("employee") or {}
    logger.info(f"Onboarding completado para {employee.get('name')} ({employee.get('employee_id')})")

    out: Dict[str, Any] = {"done": True}
    out.update(_push_event("completed", {
        "employee_id": employee.get("employee_id"),
        "name": employee.get("name"),
        "role_type": state.get("role_type"),
        "accounts_count": len(state.get("accounts") or []),
        "tools_count": len(state.get("tools_provisioned") or []),
        "permissions_count": len(state.get("permissions") or []),
        "checklist_count": len(state.get("checklist") or []),
        "notifications_count": len(state.get("notifications") or []),
    }))
    return out


# ---------------------------------------------------------------------------
# Compilación del Grafo
# ---------------------------------------------------------------------------

def compile_graph():
    """
    Construye y compila el StateGraph de onboarding.
    Flujo lineal con 8 nodos (sin loops, a diferencia del Caso 09).
    El router del Caso 09 se reemplaza aquí por lógica condicional
    dentro de los nodos (classify_role → provision_tools usa el role_type).
    """
    g = StateGraph(OnboardingState)

    g.add_node("load_employee", load_employee)
    g.add_node("classify_role", classify_role)
    g.add_node("provision_tools", provision_tools)
    g.add_node("create_corporate_accounts", create_corporate_accounts)
    g.add_node("assign_permissions", assign_permissions)
    g.add_node("generate_checklist", generate_checklist)
    g.add_node("send_welcome_package", send_welcome_package)
    g.add_node("confirm_onboarding", confirm_onboarding)

    g.add_edge(START, "load_employee")
    g.add_edge("load_employee", "classify_role")
    g.add_edge("classify_role", "provision_tools")
    g.add_edge("provision_tools", "create_corporate_accounts")
    g.add_edge("create_corporate_accounts", "assign_permissions")
    g.add_edge("assign_permissions", "generate_checklist")
    g.add_edge("generate_checklist", "send_welcome_package")
    g.add_edge("send_welcome_package", "confirm_onboarding")
    g.add_edge("confirm_onboarding", END)

    return g.compile(checkpointer=MemorySaver())
