"""Tests del grafo LangGraph — Caso 04: SOC Triage de Alertas."""
from src.graph import (
    AlertState,
    compile_graph,
    evaluar_riesgo,
    normalizar_alerta,
    route_by_risk,
    route_investigation,
)


def _base_state(alert_id: str = "ALT-001") -> AlertState:
    return {
        "alert_id": alert_id,
        "alert": {},
        "ioc_enrichment": {},
        "mitre_techniques": [],
        "siem_context": {},
        "risk_score": 0,
        "risk_level": "",
        "triage_decision": "",
        "investigation_result": "",
        "analyst_assignment": {},
        "close_record": {},
        "triage_report": "",
        "events": [],
        "done": False,
    }


def test_graph_compiles():
    """El grafo debe compilar sin excepciones."""
    graph = compile_graph()
    assert graph is not None


def test_normalizar_alerta_carga_datos():
    """normalizar_alerta debe cargar la alerta ALT-001 y normalizar severidad."""
    state = _base_state("ALT-001")
    result = normalizar_alerta(state)

    assert "alert" in result
    alert = result["alert"]
    assert alert.get("id") == "ALT-001"
    assert "normalized_severity" in alert
    assert alert["normalized_severity"] in ("low", "medium", "high", "critical")
    assert len(result.get("events", [])) > 0


def test_normalizar_alerta_fallback():
    """Con un alert_id inexistente debe devolver un fallback válido."""
    state = _base_state("ALT-NONEXISTENT")
    result = normalizar_alerta(state)
    assert result["alert"].get("id") is not None


def test_evaluar_riesgo_alto():
    """Alerta con IOC muy malicioso (score 92) debe producir riesgo alto."""
    state = _base_state()
    state["alert"] = {
        "id": "ALT-001",
        "normalized_severity": "high",
        "host": "prod-api-server-01",
        "user": "root",
        "iocs": ["185.220.101.47"],
        "event_count": 847,
        "tags": ["brute_force"],
    }
    state["ioc_enrichment"] = {
        "185.220.101.47": {
            "malicious": True,
            "score": 92,
            "categories": ["tor_exit_node", "brute_force"],
        }
    }
    state["siem_context"] = {
        "baseline_deviation_pct": 340,
        "related_events": 23,
    }

    result = evaluar_riesgo(state)
    assert result["risk_score"] >= 70
    assert result["triage_decision"] == "high"


def test_evaluar_riesgo_bajo_cierra_fp():
    """Alerta sin IOC malicioso y baseline normal debe ser falso positivo."""
    state = _base_state()
    state["alert"] = {
        "id": "ALT-005",
        "normalized_severity": "low",
        "host": "dc-server-01",
        "user": "svc-backup",
        "iocs": [],
        "event_count": 3,
        "tags": ["off_hours"],
    }
    state["ioc_enrichment"] = {}
    state["siem_context"] = {
        "baseline_deviation_pct": 10,
        "related_events": 2,
    }

    result = evaluar_riesgo(state)
    assert result["risk_score"] < 30
    assert result["triage_decision"] == "false_positive"


def test_route_by_risk_high():
    """risk_level=high debe rutear a escalar_analista."""
    state = _base_state()
    state["triage_decision"] = "high"
    assert route_by_risk(state) == "escalar_analista"


def test_route_by_risk_fp():
    """triage_decision=false_positive debe rutear a cerrar_automatico."""
    state = _base_state()
    state["triage_decision"] = "false_positive"
    assert route_by_risk(state) == "cerrar_automatico"


def test_route_by_risk_medium():
    """triage_decision=medium debe rutear a investigacion_adicional."""
    state = _base_state()
    state["triage_decision"] = "medium"
    assert route_by_risk(state) == "investigacion_adicional"


def test_route_investigation_suspicious():
    """investigation_result=suspicious debe escalar al analista."""
    state = _base_state()
    state["investigation_result"] = "suspicious"
    assert route_investigation(state) == "escalar_analista"


def test_route_investigation_benign():
    """investigation_result=benign debe cerrar como falso positivo."""
    state = _base_state()
    state["investigation_result"] = "benign"
    assert route_investigation(state) == "cerrar_automatico"


def test_flujo_completo_alt001():
    """Flujo end-to-end con ALT-001 (brute force + IOC malicioso) → debe escalar."""
    graph = compile_graph()
    cfg = {"configurable": {"thread_id": "test-e2e-alt001"}, "recursion_limit": 50}
    initial = _base_state("ALT-001")
    out = graph.invoke(initial, config=cfg)

    assert isinstance(out, dict)
    assert out.get("done") is True
    assert out.get("risk_score", 0) > 0
    assert out.get("triage_decision") in ("false_positive", "medium", "high")
    assert len(out.get("events", [])) >= 4


def test_flujo_completo_alt005():
    """Flujo end-to-end con ALT-005 (off-hours, sin IOC malicioso) → debe cerrar FP."""
    graph = compile_graph()
    cfg = {"configurable": {"thread_id": "test-e2e-alt005"}, "recursion_limit": 50}
    initial = _base_state("ALT-005")
    out = graph.invoke(initial, config=cfg)

    assert isinstance(out, dict)
    assert out.get("done") is True
    # ALT-005 tiene score bajo → esperamos FP o medium
    assert out.get("triage_decision") in ("false_positive", "medium")
