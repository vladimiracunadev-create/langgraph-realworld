"""
test_graph_flow.py — Tests de compilación y ejecución del grafo del caso 25.
"""


def test_graph_compiles():
    """El grafo debe compilar sin excepciones."""
    from src.graph import compile_graph
    graph = compile_graph()
    assert graph is not None


def test_worker_execution():
    """
    Ejecutar el grafo con task_id DDL-2026-001 debe retornar
    worker_results con exactamente 4 elementos (uno por worker).
    """
    from src.graph import compile_graph

    graph = compile_graph()
    cfg = {"configurable": {"thread_id": "test-graph-flow-1"}, "recursion_limit": 50}
    out = graph.invoke({"task_id": "DDL-2026-001", "events": []}, config=cfg)

    assert isinstance(out, dict)
    worker_results = out.get("worker_results", [])
    assert len(worker_results) == 4

    worker_types = {r["worker_type"] for r in worker_results}
    assert "financial" in worker_types
    assert "legal" in worker_types
    assert "operational" in worker_types
    assert "reputational" in worker_types


def test_all_workers_succeed():
    """Todos los workers deben completar con status 'ok' en modo DEMO."""
    from src.graph import compile_graph

    graph = compile_graph()
    cfg = {"configurable": {"thread_id": "test-graph-flow-2"}, "recursion_limit": 50}
    out = graph.invoke({"task_id": "DDL-2026-001", "events": []}, config=cfg)

    worker_results = out.get("worker_results", [])
    for wr in worker_results:
        assert wr["status"] == "ok", f"Worker {wr['worker_type']} falló: {wr['result']}"


def test_final_report_generated():
    """El informe final debe estar presente y contener datos de la empresa."""
    from src.graph import compile_graph

    graph = compile_graph()
    cfg = {"configurable": {"thread_id": "test-graph-flow-3"}, "recursion_limit": 50}
    out = graph.invoke({"task_id": "DDL-2026-001", "events": []}, config=cfg)

    final_report = out.get("final_report", "")
    assert len(final_report) > 0
    assert "TechStartup" in final_report
    assert out.get("done") is True


def test_events_accumulated():
    """Los eventos deben acumularse durante la ejecución del grafo."""
    from src.graph import compile_graph

    graph = compile_graph()
    cfg = {"configurable": {"thread_id": "test-graph-flow-4"}, "recursion_limit": 50}
    out = graph.invoke({"task_id": "DDL-2026-001", "events": []}, config=cfg)

    events = out.get("events", [])
    assert len(events) > 0

    event_types = {e["type"] for e in events}
    assert "task_loaded" in event_types
    assert "task_decomposed" in event_types
    assert "worker_completed" in event_types
    assert "report_generated" in event_types


def test_integrations_stubs():
    """Los stubs de integrations deben retornar datos válidos en modo DEMO."""
    from src.integrations import (
        financial_analysis_stub,
        legal_analysis_stub,
        operational_analysis_stub,
        reputational_analysis_stub,
    )

    fin = financial_analysis_stub("TestCo", 1_000_000)
    assert fin["mode"] == "DEMO"
    assert "risk_score" in fin
    assert "revenue_estimate_usd" in fin

    leg = legal_analysis_stub("TestCo")
    assert leg["mode"] == "DEMO"
    assert "pending_litigations" in leg

    ops = operational_analysis_stub("TestCo")
    assert ops["mode"] == "DEMO"
    assert "tech_debt_level" in ops
    assert "team_size" in ops

    rep = reputational_analysis_stub("TestCo")
    assert rep["mode"] == "DEMO"
    assert "glassdoor_rating" in rep
    assert "press_sentiment" in rep
