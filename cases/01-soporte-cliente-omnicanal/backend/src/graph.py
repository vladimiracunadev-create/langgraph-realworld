from __future__ import annotations

import operator
import time
from typing import Annotated, Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from .integrations import (
    assess_priority,
    classify_ticket_intent,
    draft_customer_response,
    find_ticket,
    knowledge_summary,
    recommended_actions,
    route_for_ticket,
)
from .settings import mode_label


class SupportState(TypedDict, total=False):
    request: dict[str, Any]
    ticket: dict[str, Any]
    intent: str
    priority: str
    route: dict[str, Any]
    actions: list[str]
    knowledge: dict[str, Any]
    response: str
    mode: str
    events: Annotated[list[dict[str, Any]], operator.add]
    done: bool


def _ts() -> int:
    return int(time.time() * 1000)


def _event(event_type: str, data: dict[str, Any]) -> dict[str, Any]:
    return {"events": [{"ts": _ts(), "type": event_type, "data": data}]}


def load_ticket(state: SupportState) -> SupportState:
    request = state.get("request") or {}
    ticket = request.get("ticket")
    if not ticket:
        ticket_id = request.get("ticket_id", "T-001")
        ticket = find_ticket(ticket_id)
    if not ticket:
        raise ValueError("Ticket no encontrado")
    out: SupportState = {"ticket": ticket, "mode": mode_label(), "done": False}
    out.update(_event("loaded", {"ticket_id": ticket.get("ticket_id"), "mode": mode_label()}))
    return out


def classify_intent(state: SupportState) -> SupportState:
    result = classify_ticket_intent(state["ticket"])
    out: SupportState = {"intent": result["intent"], "mode": result["mode"]}
    out.update(_event("classified", {"intent": result["intent"], "reason": result["reason"]}))
    return out


def prioritize_case(state: SupportState) -> SupportState:
    result = assess_priority(state["ticket"], state["intent"])
    out: SupportState = {"priority": result["priority"]}
    out.update(_event("prioritized", result))
    return out


def route_case(state: SupportState) -> SupportState:
    route = route_for_ticket(state["intent"], state["priority"])
    out: SupportState = {"route": route}
    out.update(_event("routed", route))
    return out


def prepare_actions(state: SupportState) -> SupportState:
    article = knowledge_summary(state["intent"])
    actions = recommended_actions(state["intent"], state["priority"])
    out: SupportState = {"knowledge": article, "actions": actions}
    out.update(_event("actions_prepared", {"article_id": article.get("article_id"), "count": len(actions)}))
    return out


def draft_response(state: SupportState) -> SupportState:
    response = draft_customer_response(
        state["ticket"], state["intent"], state["priority"], state["route"], state["knowledge"]
    )
    out: SupportState = {"response": response}
    out.update(_event("response_drafted", {"length": len(response)}))
    return out


def finalize_case(state: SupportState) -> SupportState:
    out: SupportState = {"done": True}
    out.update(_event("completed", {"ticket_id": state["ticket"].get("ticket_id")}))
    return out


def maybe_continue(state: SupportState) -> Literal["prepare_actions", "draft_response"]:
    route = state.get("route") or {}
    if route.get("handoff"):
        return "prepare_actions"
    return "prepare_actions"


def compile_graph():
    graph = StateGraph(SupportState)
    graph.add_node("load_ticket", load_ticket)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("prioritize_case", prioritize_case)
    graph.add_node("route_case", route_case)
    graph.add_node("prepare_actions", prepare_actions)
    graph.add_node("draft_response", draft_response)
    graph.add_node("finalize_case", finalize_case)

    graph.add_edge(START, "load_ticket")
    graph.add_edge("load_ticket", "classify_intent")
    graph.add_edge("classify_intent", "prioritize_case")
    graph.add_edge("prioritize_case", "route_case")
    graph.add_conditional_edges("route_case", maybe_continue, ["prepare_actions", "draft_response"])
    graph.add_edge("prepare_actions", "draft_response")
    graph.add_edge("draft_response", "finalize_case")
    graph.add_edge("finalize_case", END)
    return graph.compile(checkpointer=MemorySaver())
