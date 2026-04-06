from src.graph import compile_graph


def test_supported_ticket_resolves_with_runbook():
    graph = compile_graph()
    out = graph.invoke(
        {"ticket": "VPN intermitente para msmith", "events": []},
        {"configurable": {"thread_id": "case02-graph-red"}},
    )

    assert out["category"] == "red"
    assert out["approval_status"] == "BYPASSED"
    assert out["resolution_status"] == "RESOLVED"
    assert out["runbook"]["id"] == "rbk_vpn_reset"

    event_types = [event["type"] for event in out.get("events", [])]
    assert "runbook_selected" in event_types
    assert "validated" in event_types



def test_unsupported_ticket_short_circuits_runbook_execution():
    graph = compile_graph()
    out = graph.invoke(
        {"ticket": "hola buen dia", "events": []},
        {"configurable": {"thread_id": "case02-graph-unsupported"}},
    )

    assert out["category"] == "unsupported"
    assert not out.get("runbook")
    assert "problema" in out["response"].lower()
    assert "tecn" in out["response"].lower()

    event_types = [event["type"] for event in out.get("events", [])]
    assert "runbook_selected" not in event_types
    assert "executed" not in event_types
