import logging
import operator
import time
from typing import Annotated, Any, Dict, List, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from .integrations import (
    _is_live,
    check_approval_requirement,
    draft_response_llm,
    enrich_ticket_data,
    get_runbooks,
    llm_classify_issue,
    simulate_runbook_execution,
    validate_execution_llm,
)

logger = logging.getLogger(__name__)

class HelpdeskState(TypedDict, total=False):
    ticket: str
    user_info: Dict[str, Any]
    category: str
    runbook: Dict[str, Any]
    approval_status: str
    execution_log: List[str]
    resolution_status: str
    response: str
    events: Annotated[List[Dict[str, Any]], operator.add]
    mode: str

def _now_ms() -> int:
    return int(time.time() * 1000)

def _push_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {"events": [{"ts": _now_ms(), "type": event_type, "data": data}]}

def receive_ticket(state: HelpdeskState) -> Dict[str, Any]:
    mode = "LIVE" if _is_live() else "DEMO"
    out = {"mode": mode, "events": []}
    out.update(_push_event("received", {"ticket": state.get("ticket"), "mode": mode}))
    return out

def enrich_ticket(state: HelpdeskState) -> Dict[str, Any]:
    ticket = state.get("ticket", "")
    info = enrich_ticket_data(ticket)
    out = {"user_info": info}
    out.update(_push_event("enriched", {"user": info.get("user"), "equipment": info.get("equipment")}))
    return out

def classify_issue(state: HelpdeskState) -> Dict[str, Any]:
    ticket = state.get("ticket", "")
    user_info = state.get("user_info", {})
    category = llm_classify_issue(ticket, user_info)
    out = {"category": category}
    out.update(_push_event("classified", {"category": category}))
    return out

def select_runbook(state: HelpdeskState) -> Dict[str, Any]:
    cat = state.get("category", "red")
    rbs = get_runbooks()
    rb = next((r for r in rbs if r.get("category") == cat), None)
    if not rb:
        rb = rbs[0]
        
    out = {"runbook": rb}
    out.update(_push_event("runbook_selected", {"runbook_id": rb["id"], "name": rb["name"]}))
    return out

def request_approval(state: HelpdeskState) -> Dict[str, Any]:
    rb = state.get("runbook", {})
    if not rb:
        return {"approval_status": "BYPASSED"}
    status = check_approval_requirement(rb)
    out = {"approval_status": status}
    out.update(_push_event("approval_checked", {"status": status}))
    return out

def route_after_classify(state: HelpdeskState) -> Literal["select_runbook", "draft_response"]:
    if state.get("category") == "unsupported":
        return "draft_response"
    return "select_runbook"

def route_after_approval(state: HelpdeskState) -> Literal["execute_runbook", "draft_response"]:
    if state.get("approval_status") == "REJECTED":
        return "draft_response"
    return "execute_runbook"

def execute_runbook(state: HelpdeskState) -> Dict[str, Any]:
    rb = state.get("runbook", {})
    logs = simulate_runbook_execution(rb)
    out = {"execution_log": logs}
    out.update(_push_event("executed", {"lines_count": len(logs)}))
    return out

def validate_resolution(state: HelpdeskState) -> Dict[str, Any]:
    ticket = state.get("ticket", "")
    logs = state.get("execution_log", [])
    status = validate_execution_llm(ticket, logs)
    out = {"resolution_status": status}
    out.update(_push_event("validated", {"status": status}))
    return out

def draft_response(state: HelpdeskState) -> Dict[str, Any]:
    ticket = state.get("ticket", "")
    status = state.get("resolution_status", "PENDING" if state.get("category") == "unsupported" else "RESOLVED")
    rb = state.get("runbook", {})
    appr = state.get("approval_status", "")
    resp = draft_response_llm(ticket, status, rb, appr)
    out = {"response": resp}
    out.update(_push_event("responded", {"response_length": len(resp)}))
    return out

def compile_graph():
    g = StateGraph(HelpdeskState)
    g.add_node("receive_ticket", receive_ticket)
    g.add_node("enrich_ticket", enrich_ticket)
    g.add_node("classify_issue", classify_issue)
    g.add_node("select_runbook", select_runbook)
    g.add_node("request_approval", request_approval)
    g.add_node("execute_runbook", execute_runbook)
    g.add_node("validate_resolution", validate_resolution)
    g.add_node("draft_response", draft_response)

    g.add_edge(START, "receive_ticket")
    g.add_edge("receive_ticket", "enrich_ticket")
    g.add_edge("enrich_ticket", "classify_issue")
    
    # Conditional edge after classify
    g.add_conditional_edges("classify_issue", route_after_classify)
    
    g.add_edge("select_runbook", "request_approval")
    
    # Conditional edge after approval
    g.add_conditional_edges("request_approval", route_after_approval)
    
    g.add_edge("execute_runbook", "validate_resolution")
    g.add_edge("validate_resolution", "draft_response")
    g.add_edge("draft_response", END)

    return g.compile(checkpointer=MemorySaver())
