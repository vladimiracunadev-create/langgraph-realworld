"""Tests del grafo LangGraph — Caso 07: Compras y Abastecimiento."""
from src.graph import (
    CompraState,
    _po_hash,
    _score_quote,
    compile_graph,
    politica_compras_router,
    validar_solicitud,
)


def _base(solicitud_id: str = "PR-001") -> CompraState:
    return {
        "solicitud_id": solicitud_id,
        "centro_costo": "", "presupuesto_max": 0.0,
        "categoria": "", "descripcion": "",
        "items": [], "fecha_requerida": "", "responsable": "",
        "pr_validada": {},
        "suppliers_candidatos": [], "rfqs_emitidas": [],
        "cotizaciones_recibidas": [], "comparativa": [],
        "decision_politica": {}, "escalacion_comite": {},
        "recomendacion": {}, "aprobacion": {}, "orden_compra": {},
        "resumen": "",
        "events": [], "done": False,
    }


# ---------------------------------------------------------------------------
# Compilación + helpers puros
# ---------------------------------------------------------------------------

def test_graph_compiles():
    assert compile_graph() is not None


def test_score_quote_precio_bajo_alto_score():
    quote = {"precio_total": 1_000_000, "plazo_dias": 5}
    supplier = {"riesgo": 0.1}
    weights = {"precio": 0.4, "plazo": 0.3, "riesgo": 0.3}
    s = _score_quote(quote, supplier, weights, presupuesto_max=10_000_000)
    assert s["score_precio"] >= 80
    assert s["score_plazo"] >= 80
    assert s["score_riesgo"] >= 80


def test_score_quote_clamp_precio_excede():
    quote = {"precio_total": 20_000_000, "plazo_dias": 30}
    supplier = {"riesgo": 0.9}
    weights = {"precio": 0.4, "plazo": 0.3, "riesgo": 0.3}
    s = _score_quote(quote, supplier, weights, presupuesto_max=10_000_000)
    assert s["score_precio"] == 0.0


def test_po_hash_estable_y_diferencia():
    p1 = {"a": 1, "b": 2}
    p2 = {"b": 2, "a": 1}
    assert _po_hash(p1) == _po_hash(p2)
    p3 = {"a": 1, "b": 3}
    assert _po_hash(p1) != _po_hash(p3)


# ---------------------------------------------------------------------------
# Validación PR
# ---------------------------------------------------------------------------

def test_validar_solicitud_pr001_completa():
    out = validar_solicitud(_base("PR-001"))
    assert out["pr_validada"]["valida"] is True
    assert out["pr_validada"]["faltantes"] == []
    assert out["centro_costo"] == "ADM-OFICINA"
    assert out["categoria"] == "oficina"


# ---------------------------------------------------------------------------
# Router de política
# ---------------------------------------------------------------------------

def test_router_dentro_politica_preferido_pequeno():
    state = _base()
    state["pr_validada"] = {"valida": True, "faltantes": []}
    state["comparativa"] = [
        {"supplier_id": "S1", "precio_total": 2_000_000, "preferido": True, "score_total": 70.0},
    ]
    assert politica_compras_router(state) == "dentro_politica"


def test_router_requiere_comite_monto_alto():
    state = _base()
    state["pr_validada"] = {"valida": True, "faltantes": []}
    state["comparativa"] = [
        {"supplier_id": "S1", "precio_total": 60_000_000, "preferido": True, "score_total": 70.0},
    ]
    assert politica_compras_router(state) == "requiere_comite"


def test_router_requiere_comite_no_preferido_sobre_umbral():
    state = _base()
    state["pr_validada"] = {"valida": True, "faltantes": []}
    state["comparativa"] = [
        {"supplier_id": "S1", "precio_total": 8_000_000, "preferido": False, "score_total": 70.0},
    ]
    assert politica_compras_router(state) == "requiere_comite"


def test_router_pr_invalida_a_comite():
    state = _base()
    state["pr_validada"] = {"valida": False, "faltantes": ["centro_costo"]}
    state["comparativa"] = [
        {"supplier_id": "S1", "precio_total": 100_000, "preferido": True, "score_total": 70.0},
    ]
    assert politica_compras_router(state) == "requiere_comite"


# ---------------------------------------------------------------------------
# Flujos end-to-end por escenario
# ---------------------------------------------------------------------------

def test_e2e_pr001_aprobacion_automatica():
    """PR-001 → preferido, monto bajo, dentro_politica, OC emitida."""
    g = compile_graph()
    out = g.invoke(_base("PR-001"), config={"configurable": {"thread_id": "t-pr001"}})
    assert out["done"] is True
    assert out["pr_validada"]["valida"] is True
    assert out["aprobacion"]["estado"] == "APROBADA"
    assert out["orden_compra"]["emitida"] is True
    assert out["orden_compra"]["estado"] == "EMITIDA"
    assert out["recomendacion"]["preferido"] is True
    assert not out.get("escalacion_comite", {}).get("requerida", False)


def test_e2e_pr002_comparativa_cerrada():
    """PR-002 → 3 ofertas en rango cerrado, mejor es preferido, dentro_politica."""
    g = compile_graph()
    out = g.invoke(_base("PR-002"), config={"configurable": {"thread_id": "t-pr002"}})
    assert out["done"] is True
    assert len(out["comparativa"]) == 3
    top = out["comparativa"][0]
    second = out["comparativa"][1]
    # Diferencia de score acotada entre los dos primeros — comparativa cerrada
    assert (top["score_total"] - second["score_total"]) < 15
    assert out["aprobacion"]["estado"] == "APROBADA"
    assert out["orden_compra"]["emitida"] is True


def test_e2e_pr003_escalacion_comite():
    """PR-003 → monto > umbral comité, escalación obligatoria, OC con estado PENDIENTE_COMITE."""
    g = compile_graph()
    out = g.invoke(_base("PR-003"), config={"configurable": {"thread_id": "t-pr003"}})
    assert out["done"] is True
    assert out["escalacion_comite"]["requerida"] is True
    assert len(out["escalacion_comite"]["razones"]) >= 1
    assert out["aprobacion"]["estado"] == "CONDICIONAL"
    assert out["orden_compra"]["emitida"] is True
    assert out["orden_compra"]["estado"] == "PENDIENTE_COMITE"
    assert "sha256" in out["orden_compra"]


def test_e2e_eventos_completos():
    """Todos los eventos esperados se emiten en un flujo con escalación."""
    g = compile_graph()
    out = g.invoke(_base("PR-003"), config={"configurable": {"thread_id": "t-events"}})
    types = [e["type"] for e in out["events"]]
    for expected in [
        "pr_validada",
        "proveedores_buscados",
        "rfqs_emitidas",
        "cotizaciones_recibidas",
        "comparativa_lista",
        "comite_escalado",
        "recomendacion_emitida",
        "aprobacion_emitida",
        "oc_emitida",
        "compra_completada",
    ]:
        assert expected in types, f"falta evento {expected}"


def test_e2e_sin_evento_comite_en_pr001():
    """PR-001 NO debe emitir evento de escalación a comité."""
    g = compile_graph()
    out = g.invoke(_base("PR-001"), config={"configurable": {"thread_id": "t-noev"}})
    types = [e["type"] for e in out["events"]]
    assert "comite_escalado" not in types


def test_recomendacion_consistente_con_comparativa():
    """La recomendación debe coincidir con el top de la comparativa."""
    g = compile_graph()
    out = g.invoke(_base("PR-002"), config={"configurable": {"thread_id": "t-cons"}})
    top = out["comparativa"][0]
    assert out["recomendacion"]["supplier_id"] == top["supplier_id"]
    assert out["recomendacion"]["score_total"] == top["score_total"]


def test_oc_hash_presente_si_emitida():
    """OC emitida debe traer sha256 + po_numero únicos."""
    g = compile_graph()
    out = g.invoke(_base("PR-001"), config={"configurable": {"thread_id": "t-hash"}})
    oc = out["orden_compra"]
    assert oc["emitida"] is True
    assert len(oc["sha256"]) == 16
    assert oc["po_numero"].startswith("OC-PR-001-")
