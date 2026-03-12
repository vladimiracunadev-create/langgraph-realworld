from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .settings import data_dir, is_live_mode, mode_label, openai_api_key, openai_model


TEXT_INTENTS = {
    "billing": ["cobro", "factura", "pago", "reembolso", "devolucion", "cargo"],
    "technical": ["error", "caida", "no puedo", "fallando", "incidente", "bug", "acceso", "panel"],
    "shipping": ["pedido", "tracking", "envio", "despacho", "carrier", "entrega"],
    "account": ["cuenta", "contrasena", "password", "login", "usuario", "bloqueada"],
}


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_ticket_catalog() -> list[dict[str, Any]]:
    return _read_json(data_dir() / "tickets.json").get("tickets", [])


def load_kb_articles() -> dict[str, list[dict[str, Any]]]:
    return _read_json(data_dir() / "kb_articles.json").get("articles", {})


def find_ticket(ticket_id: str) -> dict[str, Any] | None:
    for item in load_ticket_catalog():
        if item.get("ticket_id") == ticket_id:
            return item
    return None


def classify_ticket_intent(ticket: dict[str, Any]) -> dict[str, Any]:
    text = f"{ticket.get('subject', '')} {ticket.get('message', '')}".lower()
    best_intent = "general"
    best_score = 0
    for intent, keywords in TEXT_INTENTS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_intent = intent
            best_score = score

    reason = (
        "Clasificacion por LLM" if is_live_mode() else "Clasificacion por reglas locales"
    )
    if is_live_mode():
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(api_key=openai_api_key(), model=openai_model(), temperature=0)
            prompt = (
                "Clasifica este ticket en una sola etiqueta entre billing, technical, shipping, account o general.\n"
                f"Asunto: {ticket.get('subject', '')}\n"
                f"Mensaje: {ticket.get('message', '')}"
            )
            result = llm.invoke(prompt)
            label = (getattr(result, "content", "") or "").strip().lower()
            if label in {"billing", "technical", "shipping", "account", "general"}:
                best_intent = label
                reason = "Clasificacion por LLM"
        except Exception:
            reason = "Clasificacion DEMO por fallback"

    return {"intent": best_intent, "mode": mode_label(), "reason": reason}


def assess_priority(ticket: dict[str, Any], intent: str) -> dict[str, Any]:
    text = f"{ticket.get('subject', '')} {ticket.get('message', '')}".lower()
    customer = ticket.get("customer", {})
    score = 0
    if customer.get("tier") == "vip":
        score += 2
    if any(word in text for word in ["urgente", "caida", "hoy", "nadie puede", "critico"]):
        score += 2
    if intent == "technical":
        score += 1
    if intent == "billing":
        score += 1

    if score >= 4:
        priority = "critical"
        sla = "15m"
    elif score >= 3:
        priority = "high"
        sla = "1h"
    elif score >= 1:
        priority = "medium"
        sla = "4h"
    else:
        priority = "low"
        sla = "24h"
    return {"priority": priority, "sla": sla}


def route_for_ticket(intent: str, priority: str) -> dict[str, Any]:
    if priority == "critical":
        return {"team": "human-escalation", "channel": "callback", "handoff": True}
    if intent == "billing":
        return {"team": "billing", "channel": "email", "handoff": True}
    if intent == "technical":
        return {"team": "technical-support", "channel": "chat", "handoff": True}
    if intent == "shipping":
        return {"team": "self-service", "channel": "email", "handoff": False}
    if intent == "account":
        return {"team": "account-support", "channel": "chat", "handoff": True}
    return {"team": "general-support", "channel": "email", "handoff": False}


def recommended_actions(intent: str, priority: str) -> list[str]:
    article = next(iter(load_kb_articles().get(intent, [])), None)
    actions = list(article.get("steps", [])) if article else []
    if priority in {"high", "critical"}:
        actions.append("Escalar al owner de guardia y registrar seguimiento")
    return actions


def knowledge_summary(intent: str) -> dict[str, Any]:
    article = next(iter(load_kb_articles().get(intent, [])), None)
    if not article:
        return {"article_id": "KB-GEN-01", "title": "Guia general", "summary": "Respuesta base"}
    return {
        "article_id": article.get("id"),
        "title": article.get("title"),
        "summary": article.get("summary"),
    }


def draft_customer_response(ticket: dict[str, Any], intent: str, priority: str, route: dict[str, Any], article: dict[str, Any]) -> str:
    customer_name = ticket.get("customer", {}).get("name", "cliente")
    base = (
        f"Hola {customer_name}, detectamos tu caso como {intent} con prioridad {priority}. "
        f"Lo estamos gestionando por el equipo {route.get('team')}. "
        f"Referencia util: {article.get('title')}."
    )
    if route.get("handoff"):
        base += " Tu caso fue derivado a una atencion asistida para reducir el tiempo de resolucion."
    else:
        base += " Te compartimos pasos de autoservicio para resolverlo mas rapido."

    if is_live_mode():
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(api_key=openai_api_key(), model=openai_model(), temperature=0.2)
            prompt = (
                "Redacta una respuesta breve, profesional y calmada para soporte al cliente en espanol.\n"
                f"Contexto: {base}\n"
                f"Mensaje original del cliente: {ticket.get('message', '')}"
            )
            result = llm.invoke(prompt)
            content = (getattr(result, "content", "") or "").strip()
            if content:
                return content
        except Exception:
            return base + " Operando en fallback DEMO por indisponibilidad temporal de LLM."
    return base
