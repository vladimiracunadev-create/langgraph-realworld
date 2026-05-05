"""Tests del grafo LangGraph — Caso 14: Finanzas - Conciliación."""
from src.graph import (
    ConciliacionState,
    _classify_tx,
    _zscore,
    compile_graph,
    matching_automatico,
    normalizar_transacciones,
)


def _base(scenario_id: str = "SCN-001") -> ConciliacionState:
    return {
        "scenario_id": scenario_id,
        "periodo": "", "descripcion_escenario": "",
        "transacciones_bancarias": [], "transacciones_contables": [],
        "normalizadas_banco": [], "normalizadas_contables": [],
        "clasificaciones": {},
        "matches": [], "unmatched_banco": [], "unmatched_contables": [],
        "outliers": [],
        "ajustes_propuestos": [], "escalaciones_auditoria": [], "partidas_en_transito": [],
        "metricas": {}, "reporte_cuadre": "", "resumen": "",
        "events": [], "done": False,
    }


def test_graph_compiles():
    assert compile_graph() is not None


# ---------------------------------------------------------------------------
# Helpers numéricos
# ---------------------------------------------------------------------------

def test_zscore_uniform():
    z = _zscore([100, 100, 100, 100])
    assert all(abs(v) < 0.01 for v in z.values())


def test_zscore_detects_outlier():
    z = _zscore([100, 102, 98, 101, 5000])
    assert max(z.values()) > 1.5


def test_classify_tx_remuneraciones():
    mapping = {"categorias": {
        "remuneraciones": {"cuenta": "5101", "centro_costo": "RRHH", "keywords": ["remuneraciones", "nómina"]},
        "otros": {"cuenta": "5999", "centro_costo": "ADM", "keywords": []},
    }}
    out = _classify_tx("Pago Remuneraciones Marzo", "Planilla", mapping)
    assert out["categoria"] == "remuneraciones"
    assert out["cuenta_contable"] == "5101"


def test_classify_tx_otros_fallback():
    mapping = {"categorias": {
        "remuneraciones": {"cuenta": "5101", "centro_costo": "RRHH", "keywords": ["remuneraciones"]},
        "otros": {"cuenta": "5999 - Otros", "centro_costo": "ADM", "keywords": []},
    }}
    out = _classify_tx("Tx desconocida", "X", mapping)
    assert out["categoria"] == "otros"


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def test_normalizar_carga_scenario():
    out = normalizar_transacciones(_base("SCN-001"))
    assert len(out["normalizadas_banco"]) == 8
    assert len(out["normalizadas_contables"]) == 8
    assert out["periodo"] == "2026-03"


def test_matching_automatico_match_perfecto():
    state = _base()
    state["normalizadas_banco"] = [
        {"id": "B1", "fecha": "2026-03-02", "monto": -1000.0,
         "descripcion": "x", "referencia": "REF1", "contraparte": "CP1"},
    ]
    state["normalizadas_contables"] = [
        {"id": "A1", "fecha": "2026-03-02", "monto": -1000.0,
         "descripcion": "x", "referencia": "REF1", "contraparte": "CP1"},
    ]
    out = matching_automatico(state)
    assert len(out["matches"]) == 1
    assert out["matches"][0]["criterio"] == "exact_match"
    assert out["matches"][0]["score"] == 1.0


def test_matching_no_match_monto_distinto():
    state = _base()
    state["normalizadas_banco"] = [
        {"id": "B1", "fecha": "2026-03-02", "monto": -1000.0,
         "descripcion": "x", "referencia": "REF1", "contraparte": "CP1"},
    ]
    state["normalizadas_contables"] = [
        {"id": "A1", "fecha": "2026-03-02", "monto": -50000.0,
         "descripcion": "x", "referencia": "REF1", "contraparte": "CP1"},
    ]
    out = matching_automatico(state)
    assert out["matches"] == []
    assert len(out["unmatched_banco"]) == 1
    assert len(out["unmatched_contables"]) == 1


# ---------------------------------------------------------------------------
# Flujos end-to-end por escenario
# ---------------------------------------------------------------------------

def test_e2e_scn001_cierre_limpio():
    """SCN-001 → 100% conciliado, riesgo verde, sin discrepancias."""
    g = compile_graph()
    out = g.invoke(_base("SCN-001"), config={"configurable": {"thread_id": "t-scn001"}})
    assert out["done"] is True
    assert out["metricas"]["riesgo"] == "verde"
    assert out["metricas"]["conciliado_pct"] == 100.0
    assert out["ajustes_propuestos"] == []
    assert out["escalaciones_auditoria"] == []
    assert out["partidas_en_transito"] == []


def test_e2e_scn002_amarillo():
    """SCN-002 → riesgo amarillo, ajustes y partidas en tránsito."""
    g = compile_graph()
    out = g.invoke(_base("SCN-002"), config={"configurable": {"thread_id": "t-scn002"}})
    assert out["done"] is True
    assert out["metricas"]["riesgo"] == "amarillo"
    assert len(out["partidas_en_transito"]) >= 1
    assert len(out["ajustes_propuestos"]) >= 1
    assert out["escalaciones_auditoria"] == []


def test_e2e_scn003_rojo_fraude():
    """SCN-003 → riesgo rojo, escalación de fraude por transferencia offshore."""
    g = compile_graph()
    out = g.invoke(_base("SCN-003"), config={"configurable": {"thread_id": "t-scn003"}})
    assert out["done"] is True
    assert out["metricas"]["riesgo"] == "rojo"
    assert len(out["escalaciones_auditoria"]) >= 1
    fraude = out["escalaciones_auditoria"][0]
    assert "panamá" in fraude["contraparte"].lower() or "llc" in fraude["contraparte"].lower()


def test_e2e_eventos_completos():
    g = compile_graph()
    out = g.invoke(_base("SCN-002"), config={"configurable": {"thread_id": "t-events"}})
    types = [e["type"] for e in out["events"]]
    for expected in [
        "transacciones_normalizadas", "transacciones_clasificadas",
        "matching_completado", "outliers_detectados",
        "ajustes_propuestos", "auditoria_escalada",
        "partidas_transito_marcadas", "reporte_generado", "cierre_completado",
    ]:
        assert expected in types, f"falta evento {expected}"


def test_metricas_consistentes_scn003():
    """Las métricas deben ser internamente consistentes."""
    g = compile_graph()
    out = g.invoke(_base("SCN-003"), config={"configurable": {"thread_id": "t-met"}})
    m = out["metricas"]
    assert m["total_matches"] == len(out["matches"])
    assert m["escalaciones"] == len(out["escalaciones_auditoria"])
    assert m["ajustes_pendientes"] == len(out["ajustes_propuestos"])
    assert 0 <= m["conciliado_pct"] <= 100
