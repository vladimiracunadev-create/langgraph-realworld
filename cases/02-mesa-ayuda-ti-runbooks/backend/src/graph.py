import logging
import operator
import time
from typing import Annotated, Any, Dict, List

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from .integrations import (
    _is_live,
    draft_response_llm,
    get_runbooks,
    llm_classify_issue,
    simulate_runbook_execution,
    validate_execution_llm,
)

logger = logging.getLogger(__name__)

class HelpdeskState(TypedDict, total=False):
    ticket: str
    category: str
    runbook: Dict[str, Any]
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

def classify_issue(state: HelpdeskState) -> Dict[str, Any]:
    ticket = state.get("ticket", "")
    category = llm_classify_issue(ticket)
    out = {"category": category}
    out.update(_push_event("classified", {"category": category}))
    return out

def select_runbook(state: HelpdeskState) -> Dict[str, Any]:
    cat = state.get("category", "red")
    rbs = get_runbooks()
    # Find first runbook that matches category
    rb = next((r for r in rbs if r.get("category") == cat), None)
    
    if not rb:
        # Fallback to first if none matches
        rb = rbs[0]
        
    out = {"runbook": rb}
    out.update(_push_event("runbook_selected", {"runbook_id": rb["id"], "name": rb["name"]}))
    return out

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
    status = state.get("resolution_status", "RESOLVED")
    rb = state.get("runbook", {})
    resp = draft_response_llm(ticket, status, rb)
    out = {"response": resp}
    out.update(_push_event("responded", {"response_length": len(resp)}))
    return out

def compile_graph():
    g = StateGraph(HelpdeskState)
    g.add_node("receive_ticket", receive_ticket)
    g.add_node("classify_issue", classify_issue)
    g.add_node("select_runbook", select_runbook)
    g.add_node("execute_runbook", execute_runbook)
    g.add_node("validate_resolution", validate_resolution)
    g.add_node("draft_response", draft_response)

    g.add_edge(START, "receive_ticket")
    g.add_edge("receive_ticket", "classify_issue")
    g.add_edge("classify_issue", "select_runbook")
    g.add_edge("select_runbook", "execute_runbook")
    g.add_edge("execute_runbook", "validate_resolution")
    g.add_edge("validate_resolution", "draft_response")
    g.add_edge("draft_response", END)

    return g.compile(checkpointer=MemorySaver())
