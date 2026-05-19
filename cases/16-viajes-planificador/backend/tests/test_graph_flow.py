"""Tests del grafo LangGraph — Caso 16: Planificador de Viajes."""
from src.graph import (
    ViajeState,
    buscar_alojamiento,
    buscar_movilidad,
    buscar_vuelos,
    compile_graph,
    cumple_restricciones_router,
    decision_viajero_router,
    ensamblar_itinerario,
    parsear_requisitos,
    politica_router,
    validar_presupuesto,
    verificar_politica_viajes,
)


def _base(viaje_id: str = "V-001") -> ViajeState:
    return {
        "viaje_id": viaje_id, "requisitos": {}, "politica": {}, "politica_ok": False,
        "motivo_rechazo": "", "vuelos": {}, "alojamiento": {}, "movilidad": {},
        "itinerario": {}, "costo_total": 0, "dentro_presupuesto": False,
        "iter_optimizacion": 0, "iter_ajuste": 0, "decision_viajero": "aprobar",
        "ajuste_solicitado": "", "brief_final": "", "estado_final": "",
        "audit_trail": [], "metricas": {}, "events": [], "done": False,
    }


def _hidrata_hasta_politica(viaje_id: str) -> ViajeState:
    state = _base(viaje_id)
    out = parsear_requisitos(state)
    state.update({k: v for k, v in out.items() if k != "events"})
    return state


def _hidrata_hasta_busqueda(viaje_id: str) -> ViajeState:
    state = _hidrata_hasta_politica(viaje_id)
    pol = verificar_politica_viajes(state)
    state.update({k: v for k, v in pol.items() if k != "events"})
    return state


def test_graph_compiles():
    assert compile_graph() is not None


# Nodos individuales

def test_parsear_v001():
    out = parsear_requisitos(_base("V-001"))
    assert out["requisitos"]["origen"] == "SCL"
    assert out["requisitos"]["destino"] == "LIM"
    assert out["requisitos"]["noches"] == 3
    assert out["iter_optimizacion"] == 0
    assert out["iter_ajuste"] == 0


def test_verificar_politica_v001_ok():
    state = _hidrata_hasta_politica("V-001")
    out = verificar_politica_viajes(state)
    assert out["politica_ok"] is True
    assert out["motivo_rechazo"] == ""


def test_verificar_politica_v004_rechaza_ciudad_restringida():
    state = _hidrata_hasta_politica("V-004")
    out = verificar_politica_viajes(state)
    assert out["politica_ok"] is False
    assert out["motivo_rechazo"] == "ciudad_restringida_por_politica"


def test_buscar_vuelos_v001_elige_mas_barato():
    state = _hidrata_hasta_busqueda("V-001")
    out = buscar_vuelos(state)
    vuelos = out["vuelos"]
    # FL-003 (Sky) es el más barato en SCL-LIM economy: 210000
    assert vuelos["ida"]["id"] == "FL-003"
    assert vuelos["costo_total_clp"] == 420000


def test_buscar_alojamiento_v001_categoria_minima():
    state = _hidrata_hasta_busqueda("V-001")
    out = buscar_alojamiento(state)
    aloj = out["alojamiento"]
    # HT-LIM-02 es cat 3, el más barato a 65000 × 3
    assert aloj["hotel"]["id"] == "HT-LIM-02"
    assert aloj["costo_total_clp"] == 195000


def test_buscar_movilidad_v001_transfer_y_local():
    state = _hidrata_hasta_busqueda("V-001")
    out = buscar_movilidad(state)
    mov = out["movilidad"]
    # 18000 + 25000×3 = 93000
    assert mov["costo_total_clp"] == 93000


def test_ensamblar_sin_descuento():
    state = _hidrata_hasta_busqueda("V-001")
    state["vuelos"] = buscar_vuelos(state)["vuelos"]
    state["alojamiento"] = buscar_alojamiento(state)["alojamiento"]
    state["movilidad"] = buscar_movilidad(state)["movilidad"]
    state["iter_optimizacion"] = 0
    out = ensamblar_itinerario(state)
    assert out["costo_total"] == 420000 + 195000 + 93000
    assert out["itinerario"]["desglose_clp"]["descuento_corporativo_pct"] == 0.0


def test_ensamblar_con_descuento_optimizacion():
    state = _hidrata_hasta_busqueda("V-002")
    state["vuelos"] = buscar_vuelos(state)["vuelos"]
    state["alojamiento"] = buscar_alojamiento(state)["alojamiento"]
    state["movilidad"] = buscar_movilidad(state)["movilidad"]
    state["iter_optimizacion"] = 1
    out = ensamblar_itinerario(state)
    # Costo bruto V-002: 980000*2 + 85000*5 + (35000 + 18000*5) = 1960000 + 425000 + 125000 = 2510000
    # Con 30% descuento: 1757000
    assert out["costo_total"] == 1757000


def test_validar_presupuesto_v001_dentro():
    state = _hidrata_hasta_busqueda("V-001")
    state["costo_total"] = 700000
    out = validar_presupuesto(state)
    assert out["dentro_presupuesto"] is True


def test_validar_presupuesto_fuera():
    state = _hidrata_hasta_busqueda("V-001")
    state["costo_total"] = 9000000
    out = validar_presupuesto(state)
    assert out["dentro_presupuesto"] is False


# Routers

def test_politica_router_ok():
    state = _base()
    state["politica_ok"] = True
    assert politica_router(state) == "buscar_vuelos"


def test_politica_router_rechaza():
    state = _base()
    state["politica_ok"] = False
    assert politica_router(state) == "rechazar_viaje"


def test_cumple_restricciones_router_optimiza_si_fuera():
    state = _base()
    state["politica"] = {"max_iter_optimizacion": 2}
    state["dentro_presupuesto"] = False
    state["iter_optimizacion"] = 0
    assert cumple_restricciones_router(state) == "optimizar_costos"


def test_cumple_restricciones_router_presenta_si_cumple():
    state = _base()
    state["politica"] = {"max_iter_optimizacion": 2}
    state["dentro_presupuesto"] = True
    assert cumple_restricciones_router(state) == "presentar_itinerario"


def test_cumple_restricciones_router_presenta_si_tope():
    state = _base()
    state["politica"] = {"max_iter_optimizacion": 2}
    state["dentro_presupuesto"] = False
    state["iter_optimizacion"] = 2
    assert cumple_restricciones_router(state) == "presentar_itinerario"


def test_decision_router_aprueba_directo():
    state = _base()
    state["politica"] = {"max_iter_ajuste": 2}
    state["decision_viajero"] = "aprobar"
    assert decision_viajero_router(state) == "generar_brief_viaje"


def test_decision_router_solicita_ajuste():
    state = _base()
    state["politica"] = {"max_iter_ajuste": 2}
    state["decision_viajero"] = "ajustar"
    state["iter_ajuste"] = 0
    assert decision_viajero_router(state) == "aplicar_ajuste_iterativo"


def test_decision_router_aprueba_tras_un_ajuste():
    state = _base()
    state["politica"] = {"max_iter_ajuste": 2}
    state["decision_viajero"] = "ajustar"
    state["iter_ajuste"] = 1
    assert decision_viajero_router(state) == "generar_brief_viaje"


# Flujos end-to-end

def test_e2e_v001_aprobado():
    g = compile_graph()
    out = g.invoke(_base("V-001"), config={"configurable": {"thread_id": "t-v001"}})
    assert out["done"] is True
    assert out["estado_final"] == "aprobado"
    assert out["iter_optimizacion"] == 0
    assert out["iter_ajuste"] == 0
    assert out["dentro_presupuesto"] is True


def test_e2e_v002_loop_optimizacion():
    g = compile_graph()
    out = g.invoke(_base("V-002"), config={"configurable": {"thread_id": "t-v002"}})
    assert out["done"] is True
    assert out["estado_final"] == "aprobado"
    assert out["iter_optimizacion"] >= 1
    assert out["dentro_presupuesto"] is True


def test_e2e_v003_loop_ajuste_viajero():
    g = compile_graph()
    out = g.invoke(_base("V-003"), config={"configurable": {"thread_id": "t-v003"}})
    assert out["done"] is True
    assert out["estado_final"] == "aprobado"
    assert out["iter_ajuste"] >= 1
    # El ajuste subió la categoría mínima de hotel a 4
    hotel = out["itinerario"]["alojamiento"]["hotel"]
    assert hotel["categoria"] >= 4


def test_e2e_v004_rechazado_politica():
    g = compile_graph()
    out = g.invoke(_base("V-004"), config={"configurable": {"thread_id": "t-v004"}})
    assert out["done"] is True
    assert out["estado_final"] == "rechazado"
    # No debe haber buscado vuelos
    assert out["vuelos"] == {}


def test_e2e_eventos_completos_v001():
    g = compile_graph()
    out = g.invoke(_base("V-001"), config={"configurable": {"thread_id": "t-events"}})
    types = [e["type"] for e in out["events"]]
    for esperado in [
        "requisitos_parseados", "politica_verificada", "vuelos_buscados",
        "alojamiento_buscado", "movilidad_buscada", "itinerario_ensamblado",
        "presupuesto_validado", "itinerario_presentado", "brief_generado",
        "auditoria_registrada",
    ]:
        assert esperado in types, f"falta evento {esperado}"


def test_costo_es_determinista():
    """Mismo input → mismo costo (determinismo DEMO)."""
    g1 = compile_graph()
    g2 = compile_graph()
    o1 = g1.invoke(_base("V-001"), config={"configurable": {"thread_id": "t-det-1"}})
    o2 = g2.invoke(_base("V-001"), config={"configurable": {"thread_id": "t-det-2"}})
    assert o1["costo_total"] == o2["costo_total"]
    assert o1["itinerario"]["vuelos"]["ida"]["id"] == o2["itinerario"]["vuelos"]["ida"]["id"]
