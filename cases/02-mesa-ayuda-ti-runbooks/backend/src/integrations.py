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

def llm_classify_issue(ticket: str) -> str:
    """Clasifica el problema usando IA si está LIVE, de lo contrario mock."""
    if not _is_live():
        # Fallback trivial
        tk = ticket.lower()
        if "vpn" in tk or "red" in tk or "internet" in tk:
            return "red"
        elif "bloque" in tk or "pass" in tk or "acceso" in tk:
            return "accesos"
        elif "qa" in tk or "servidor" in tk or "500" in tk:
            return "infra"
        else:
            return "hardware"
            
    # Modo LIVE
    llm = ChatOpenAI(temperature=0.0, model=LLM_MODEL)
    prompt = (
        f"Clasifica el siguiente ticket de soporte en una de estas categorías: "
        f"red, accesos, infra, hardware. Responde SOLO con la categoría.\nTicket: {ticket}"
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    cat = str(resp.content).strip().lower()
    if cat not in ["red", "accesos", "infra", "hardware"]:
        return "red" # safe default
    return cat

def simulate_runbook_execution(runbook: Dict[str, Any]) -> List[str]:
    """Genera logs falsos simulando la ejecución del runbook."""
    logs = []
    logs.append(f"> Iniciando runbook: {runbook['name']} ({runbook['id']})")
    
    for step in runbook.get("steps", []):
        logs.append(f"> Ejecutando: {step}...")
        # Simulación de un delay mínimo para UX
        logs.append(f"  [OK] Paso completado con éxito.")
        
    logs.append("> Runbook finalizado. Status: SUCCESS")
    return logs

def validate_execution_llm(ticket: str, logs: List[str]) -> str:
    """Evalúa los logs contra el problema para ver si cuadra. Usa IA en LIVE."""
    log_text = "\n".join(logs)
    if not _is_live():
        # Mock validation
        if "SUCCESS" in log_text:
            return "RESOLVED"
        return "ESCALATED"

    llm = ChatOpenAI(temperature=0.0, model=LLM_MODEL)
    prompt = (
        f"El usuario reportó: '{ticket}'.\n"
        f"Se ejecutaron estos comandos SRE con el siguiente resultado:\n{log_text}\n"
        f"¿El problema parece resuelto? Responde SOLO con 'RESOLVED' o 'ESCALATED'."
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    val = str(resp.content).strip().upper()
    return val if val in ["RESOLVED", "ESCALATED"] else "RESOLVED"

def draft_response_llm(ticket: str, status: str, runbook: Dict[str, Any]) -> str:
    """Redacta mensaje para el cliente."""
    if not _is_live():
        if status == "RESOLVED":
            return f"Hola! Hemos ejecutado el procedimiento automático '{runbook['name']}' y tu problema debería estar resuelto. Confírmame si puedes validar."
        else:
            return f"Hola. Intentamos correr '{runbook['name']}' pero necesitamos escalar tu caso al nivel 2. Tu número de ticket es #TI-{random.randint(1000, 9999)}."

    llm = ChatOpenAI(temperature=0.7, model=LLM_MODEL)
    prompt = (
        f"Eres un agente de mesa de ayuda TI. "
        f"El usuario dijo: '{ticket}'. "
        f"El estado actual post-runbook ({runbook['name']}) es '{status}'. "
        f"Redacta una respuesta amable, profesional y concisa (max 2 párrafos) al usuario informando lo sucedido."
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    return str(resp.content)
