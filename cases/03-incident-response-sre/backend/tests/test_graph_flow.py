from src.graph import IncidentState, classify_severity, compile_graph


def test_graph_compiles():
    """El grafo debe compilar sin lanzar excepciones."""
    graph = compile_graph()
    assert graph is not None


def test_classify_severity():
    """Con un incidente P1, el nodo classify_severity debe devolver severity='P1'."""
    state: IncidentState = {
        "incident_id": "INC-001",
        "incident": {
            "id": "INC-001",
            "title": "Incidente crítico de prueba",
            "severity": "P1",
            "service": "payments-api",
            "description": "Test",
            "metrics": {},
            "timestamp": "2026-04-09T00:00:00Z",
        },
        "signals": [],
        "severity": "",
        "runbook": {},
        "approval_pending": False,
        "approved": False,
        "actions_taken": [],
        "recovery": {},
        "postmortem": "",
        "events": [],
        "done": False,
    }
    result = classify_severity(state)
    assert result["severity"] == "P1"
