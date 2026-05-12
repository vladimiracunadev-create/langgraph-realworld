"""Tests del grafo LangGraph — Caso 15: E-commerce Postventa."""
from src.graph import (
    PostventaState,
    _label_hash,
    _parse_date,
    clasificar_intencion,
    compile_graph,
    elegibilidad_router,
    intencion_router,
    stock_router,
)


def _base(order_id: str = "ORD-001", intent: str = "") -> PostventaState:
    return {
        "order_id": order_id,
        "intent_input": intent,
        "pedido": {}, "intencion": "",
        "tracking": {}, "elegibilidad": {}, "etiqueta": {},
        "stock": {}, "cambio_resultado": {}, "escalacion": {},
        "respuesta": "", "resumen": "",
        "events": [], "done": False,
    }


# ---------------------------------------------------------------------------
# Helpers puros
# ---------------------------------------------------------------------------

def test_graph_compiles():
    assert compile_graph() is not None


def test_parse_date():
    assert _parse_date("2026-05-11") is not None
    assert _parse_date("") is None
    assert _parse_date("invalido") is None


def test_label_hash_estable():
    a = {"x": 1, "y": 2}
    b = {"y": 2, "x": 1}
    assert _label_hash(a) == _label_hash(b)
    c = {"x": 1, "y": 3}
    assert _label_hash(a) != _label_hash(c)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

def test_intencion_router_tres_vias():
    s = _base(); s["intencion"] = "seguimiento"
    assert intencion_router(s) == "seguimiento"
    s["intencion"] = "devolucion"
    assert intencion_router(s) == "devolucion"
    s["intencion"] = "cambio"
    assert intencion_router(s) == "cambio"


def test_intencion_router_fallback():
    s = _base(); s["intencion"] = "ruido"
    assert intencion_router(s) == "seguimiento"


def test_elegibilidad_router_ambos():
    s = _base(); s["elegibilidad"] = {"elegible": True}
    assert elegibilidad_router(s) == "elegible"
    s["elegibilidad"] = {"elegible": False}
    assert elegibilidad_router(s) == "no_elegible"


def test_stock_router_ambos():
    s = _base(); s["stock"] = {"todos_disponibles": True}
    assert stock_router(s) == "disponible"
    s["stock"] = {"todos_disponibles": False}
    assert stock_router(s) == "agotado"


def test_clasificar_usa_intent_input_si_valido():
    s = _base(intent="devolucion")
    s["pedido"] = {"intent": "seguimiento"}
    out = clasificar_intencion(s)
    assert out["intencion"] == "devolucion"


def test_clasificar_usa_pedido_si_input_vacio():
    s = _base(intent="")
    s["pedido"] = {"intent": "cambio"}
    out = clasificar_intencion(s)
    assert out["intencion"] == "cambio"


def test_clasificar_fallback_default():
    s = _base(intent="")
    s["pedido"] = {}
    out = clasificar_intencion(s)
    assert out["intencion"] == "seguimiento"


# ---------------------------------------------------------------------------
# Flujos end-to-end por escenario
# ---------------------------------------------------------------------------

def test_e2e_ord001_seguimiento_resuelto():
    """ORD-001 → camino seguimiento → tracking entregado al cliente."""
    g = compile_graph()
    out = g.invoke(_base("ORD-001"), config={"configurable": {"thread_id": "t-001"}})
    assert out["done"] is True
    assert out["intencion"] == "seguimiento"
    assert out["tracking"]["encontrado"] is True
    assert out["tracking"]["eta"]
    assert "BX-987654321" in out["respuesta"] or "tracking" in out["respuesta"].lower() or out["tracking"]["codigo"] in out["respuesta"]


def test_e2e_ord002_devolucion_elegible_etiqueta_emitida():
    """ORD-002 → devolución dentro de plazo → etiqueta emitida con hash."""
    g = compile_graph()
    out = g.invoke(_base("ORD-002"), config={"configurable": {"thread_id": "t-002"}})
    assert out["done"] is True
    assert out["intencion"] == "devolucion"
    assert out["elegibilidad"]["elegible"] is True
    assert out["etiqueta"]["emitida"] is True
    assert len(out["etiqueta"]["sha256"]) == 16
    assert out["etiqueta"]["etiqueta_id"].startswith("RET-ORD-002-")
    assert not out.get("escalacion", {}).get("requerida", False)


def test_e2e_ord003_devolucion_no_elegible_escala_humano():
    """ORD-003 → fuera de plazo + categoría no devolvible → derivación humana."""
    g = compile_graph()
    out = g.invoke(_base("ORD-003"), config={"configurable": {"thread_id": "t-003"}})
    assert out["done"] is True
    assert out["intencion"] == "devolucion"
    assert out["elegibilidad"]["elegible"] is False
    assert len(out["elegibilidad"]["razones"]) >= 1
    assert out["escalacion"]["requerida"] is True
    assert not out.get("etiqueta", {}).get("emitida", False)


def test_e2e_ord004_cambio_stock_disponible():
    """ORD-004 → cambio dentro de plazo, SKU destino con stock → procesa cambio."""
    g = compile_graph()
    out = g.invoke(_base("ORD-004"), config={"configurable": {"thread_id": "t-004"}})
    assert out["done"] is True
    assert out["intencion"] == "cambio"
    assert out["stock"]["todos_disponibles"] is True
    assert out["cambio_resultado"]["exitoso"] is True
    assert len(out["cambio_resultado"]["reservas"]) == 1
    assert not out.get("escalacion", {}).get("requerida", False)


def test_e2e_ord005_cambio_sin_stock_escala():
    """ORD-005 → SKU destino sin stock → derivación humana."""
    g = compile_graph()
    out = g.invoke(_base("ORD-005"), config={"configurable": {"thread_id": "t-005"}})
    assert out["done"] is True
    assert out["intencion"] == "cambio"
    assert out["stock"]["todos_disponibles"] is False
    assert out["escalacion"]["requerida"] is True
    assert not out.get("cambio_resultado", {}).get("exitoso", False)


def test_e2e_intent_override_via_input():
    """intent_input fuerza el camino aunque el pedido traiga otra intent."""
    g = compile_graph()
    out = g.invoke(
        _base("ORD-001", intent="devolucion"),
        config={"configurable": {"thread_id": "t-override"}},
    )
    assert out["done"] is True
    assert out["intencion"] == "devolucion"


def test_e2e_eventos_pipeline_seguimiento():
    g = compile_graph()
    out = g.invoke(_base("ORD-001"), config={"configurable": {"thread_id": "t-ev-seg"}})
    types = [e["type"] for e in out["events"]]
    for expected in [
        "solicitud_recibida",
        "pedido_consultado",
        "intencion_clasificada",
        "tracking_consultado",
        "respuesta_redactada",
        "caso_completado",
    ]:
        assert expected in types, f"falta evento {expected}"


def test_e2e_eventos_pipeline_devolucion_elegible():
    g = compile_graph()
    out = g.invoke(_base("ORD-002"), config={"configurable": {"thread_id": "t-ev-dev"}})
    types = [e["type"] for e in out["events"]]
    for expected in [
        "elegibilidad_evaluada",
        "etiqueta_emitida",
        "respuesta_redactada",
        "caso_completado",
    ]:
        assert expected in types, f"falta evento {expected}"


def test_e2e_eventos_pipeline_cambio_disponible():
    g = compile_graph()
    out = g.invoke(_base("ORD-004"), config={"configurable": {"thread_id": "t-ev-cam"}})
    types = [e["type"] for e in out["events"]]
    for expected in [
        "stock_verificado",
        "cambio_procesado",
        "respuesta_redactada",
        "caso_completado",
    ]:
        assert expected in types, f"falta evento {expected}"


def test_e2e_resumen_resuelto_o_derivado():
    g = compile_graph()
    for oid, esperado in [("ORD-001", "RESUELTO"), ("ORD-002", "RESUELTO"),
                           ("ORD-003", "DERIVADO"), ("ORD-004", "RESUELTO"),
                           ("ORD-005", "DERIVADO")]:
        out = g.invoke(_base(oid), config={"configurable": {"thread_id": f"t-r-{oid}"}})
        assert esperado in out["resumen"], f"{oid} esperaba {esperado}"


def test_e2e_respuesta_no_vacia_en_todos_los_caminos():
    g = compile_graph()
    for oid in ["ORD-001", "ORD-002", "ORD-003", "ORD-004", "ORD-005"]:
        out = g.invoke(_base(oid), config={"configurable": {"thread_id": f"t-rr-{oid}"}})
        assert out["respuesta"], f"{oid} sin respuesta"
        assert len(out["respuesta"]) > 50
