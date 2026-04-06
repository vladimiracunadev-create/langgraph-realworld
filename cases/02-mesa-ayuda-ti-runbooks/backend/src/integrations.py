import json
import logging
import os
import random
import time
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# Fallback models si hay LLM
LLM_MODEL = "gpt-3.5-turbo"

def _is_live() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))

def get_runbooks() -> List[Dict[str, Any]]:
    from .settings import data_dir
    with open(os.path.join(data_dir(), "runbooks.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def get_inventory() -> List[Dict[str, Any]]:
    from .settings import data_dir
    with open(os.path.join(data_dir(), "inventory.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def enrich_ticket_data(ticket: str) -> Dict[str, Any]:
    """Busca al usuario en el inventario o asigna uno por defecto."""
    inv = get_inventory()
    # Si el ticket menciona jrodriguez o msmith
    tk = ticket.lower()
    if "msmith" in tk:
        user = next(u for u in inv if u["user"] == "msmith")
    elif "jrodriguez" in tk:
        user = next(u for u in inv if u["user"] == "jrodriguez")
    else:
        user = random.choice(inv)
    return user

def llm_classify_issue(ticket: str, user_info: Dict[str, Any]) -> str:
    """Clasifica considerando ticket y contexto del usuario."""
    if not _is_live():
        tk = ticket.lower()
        if "hola" in tk or "buenos dia" in tk or "saludo" in tk:
            return "unsupported"
        if "vpn" in tk or "red" in tk or "internet" in tk:
            return "red"
        elif "bloque" in tk or "pass" in tk or "acceso" in tk or "locked" in user_info.get("status", ""):
            return "accesos"
        elif "qa" in tk or "servidor" in tk or "500" in tk:
            return "infra"
        else:
            return "hardware"
            
    llm = ChatOpenAI(temperature=0.0, model=LLM_MODEL)
    prompt = (
        "Clasifica el ticket en: red, accesos, infra, hardware, o unsupported "
        "(si es un saludo o no tiene sentido TI).\n"
        f"Contexto User: {user_info}\nTicket: {ticket}\nResponde SOLO con la categoría."
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    cat = str(resp.content).strip().lower()
    if cat not in ["red", "accesos", "infra", "hardware", "unsupported"]:
        return "unsupported"
    return cat

def check_approval_requirement(runbook: Dict[str, Any]) -> str:
    """Simula una evaluación de riesgo (HITL)."""
    cat = runbook.get("category", "")
    # Simulamos que infra y accesos requieren aprobación
    if cat in ["infra", "accesos"]:
        # Mockeamos una aprobación automática (como si un manager diera OK en Slack)
        # o un rechazo con un 10% de prob.
        time.sleep(1) # pausa dramatica UX
        return "APPROVED" if random.random() > 0.1 else "REJECTED"
    return "BYPASSED" # No requiere

def simulate_runbook_execution(runbook: Dict[str, Any]) -> List[str]:
    logs = []
    logs.append(f"> Iniciando runbook: {runbook['name']} ({runbook['id']})")
    
    for step in runbook.get("steps", []):
        logs.append(f"> Ejecutando: {step}...")
        logs.append("  [OK] Paso completado.")
        
    logs.append("> Runbook finalizado. Status: SUCCESS")
    return logs

def validate_execution_llm(ticket: str, logs: List[str]) -> str:
    log_text = "\n".join(logs)
    if not _is_live():
        if "SUCCESS" in log_text:
            return "RESOLVED"
        return "ESCALATED"

    llm = ChatOpenAI(temperature=0.0, model=LLM_MODEL)
    prompt = (
        f"El usuario reportó: '{ticket}'.\n"
        f"Logs:\n{log_text}\n"
        f"¿Problema resuelto? Responde SOLO 'RESOLVED' o 'ESCALATED'."
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    val = str(resp.content).strip().upper()
    return val if val in ["RESOLVED", "ESCALATED"] else "RESOLVED"

def draft_response_llm(ticket: str, status: str, runbook: Dict[str, Any], approval: str) -> str:
    if not runbook and status != "RESOLVED": 
        # Es unsupported
        return (
            "¡Hola! Soy tu SRE Assistant. Por favor, indícame cuál es tu problema tecnológico "
            "(ej: fallos de red, accesos o sistemas) para poder ejecutar un diagnóstico."
        )
        
    if approval == "REJECTED":
        return (
            f"El procedimiento '{runbook['name']}' requería autorización pero fue RECHAZADO por L2. "
            "Mantenemos el ticket en revisión manual."
        )
        
    if not _is_live():
        if status == "RESOLVED":
            return (
                f"Ejecutamos con éxito '{runbook['name']}'. "
                "Por favor confirma si el servicio volvió a la normalidad."
            )
        else:
            return f"Hubo fallos menores. Tu caso ha sido escalado #TI-{random.randint(1000, 9999)}."

    llm = ChatOpenAI(temperature=0.7, model=LLM_MODEL)
    prompt = (
        f"Agente TI. Ticket: '{ticket}'. Runbook: '{runbook['name']}'. "
        f"Status: '{status}'. Redacta una respuesta muy corta al usuario informando la acción tomada."
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    return str(resp.content)
