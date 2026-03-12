from src.graph import (
    classify_intent,
    draft_response,
    finalize_case,
    load_ticket,
    prepare_actions,
    prioritize_case,
    route_case,
)


def test_graph_flow_demo_ticket():
    state = load_ticket({"request": {"ticket_id": "T-001"}, "events": []})
    assert state["ticket"]["ticket_id"] == "T-001"

    state.update(classify_intent(state))
    assert state["intent"] in {"billing", "technical", "shipping", "account", "general"}

    state.update(prioritize_case(state))
    assert state["priority"] in {"low", "medium", "high", "critical"}

    state.update(route_case(state))
    assert "team" in state["route"]

    state.update(prepare_actions(state))
    assert len(state["actions"]) >= 1
    assert "article_id" in state["knowledge"]

    state.update(draft_response(state))
    assert len(state["response"]) > 20

    state.update(finalize_case(state))
    assert state["done"] is True

    events = state.get("events") or []
    assert any(evt["type"] == "completed" for evt in events)
