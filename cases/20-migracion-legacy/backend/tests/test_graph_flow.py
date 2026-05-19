"""Tests del grafo LangGraph — Caso 20: Migración Legacy."""
from src.graph import (
    MigracionState,
    _orden_topologico,
    analizar_codigo_legacy,
    compile_graph,
    ejecutar_tests,
    mapear_dependencias,
    migracion_completa_router,
    planificar_migracion,
    refactorizar_modulo,
    resultado_tests_router,
    seleccionar_lote,
)


def _base(proyecto_id: str = "P-001") -> MigracionState:
    return {
        "proyecto_id": proyecto_id, "proyecto": {}, "dependencias": {},
        "plan_migracion": [], "lote_actual": "", "lotes_completados": [],
        "lotes_pendientes": [], "codigo_refactorizado": {}, "tests_generados": {},
        "resultado_tests": {}, "iter_regresion": {}, "progreso": [],
        "regresiones": [], "reporte_final": "", "estado_final": "",
        "metricas": {}, "events": [], "done": False,
    }


def test_graph_compiles():
    assert compile_graph() is not None


# Helpers ---------------------------------------------------------------

def test_orden_topologico_respeta_dependencias():
    deps = {"a": [], "b": ["a"], "c": ["b"]}
    orden = _orden_topologico(["c", "b", "a"], deps)
    assert orden.index("a") < orden.index("b") < orden.index("c")


def test_orden_topologico_modulo_sin_deps_va_primero():
    deps = {"clientes": ["auth"], "auth": [], "facturacion": ["clientes", "auth"]}
    orden = _orden_topologico(["clientes", "auth", "facturacion"], deps)
    assert orden[0] == "auth"
    assert orden[-1] == "facturacion"


# Nodos -----------------------------------------------------------------

def test_analizar_p001():
    out = analizar_codigo_legacy(_base("P-001"))
    assert out["proyecto"]["lenguaje_origen"] == "VB6"
    assert out["proyecto"]["lenguaje_destino"] == "Python"
    assert "facturacion" in out["proyecto"]["modulos"]


def test_mapear_dependencias_p001():
    state = _base("P-001")
    state["proyecto"] = analizar_codigo_legacy(state)["proyecto"]
    out = mapear_dependencias(state)
    assert "auth" in out["dependencias"]
    assert out["dependencias"]["auth"] == []


def test_planificar_migracion_p001():
    state = _base("P-001")
    state["proyecto"] = analizar_codigo_legacy(state)["proyecto"]
    state["dependencias"] = mapear_dependencias(state)["dependencias"]
    out = planificar_migracion(state)
    plan = out["plan_migracion"]
    assert len(plan) == 4
    nombres = [p["modulo"] for p in plan]
    assert nombres.index("auth") < nombres.index("clientes")
    assert nombres.index("clientes") < nombres.index("facturacion")


def test_seleccionar_lote_toma_el_primer_pendiente():
    state = _base("P-001")
    state["lotes_pendientes"] = ["auth", "clientes", "facturacion"]
    out = seleccionar_lote(state)
    assert out["lote_actual"] == "auth"
    assert out["iter_regresion"]["auth"] == 0


def test_refactorizar_modulo_carga_codigo():
    state = _base("P-001")
    state["lote_actual"] = "auth"
    out = refactorizar_modulo(state)
    assert "auth" in out["codigo_refactorizado"]
    assert "def login" in out["codigo_refactorizado"]["auth"]["codigo_destino"]


def test_ejecutar_tests_pass_directo():
    state = _base("P-001")
    state["lote_actual"] = "auth"
    state["tests_generados"] = {"auth": ["t1", "t2"]}
    state["iter_regresion"] = {"auth": 0}
    out = ejecutar_tests(state)
    assert out["resultado_tests"]["auth"]["ok"] is True
    assert out["resultado_tests"]["auth"]["detalle"] == "pass_directo"


def test_ejecutar_tests_falla_inicial_p002_transferencias():
    state = _base("P-002")
    state["lote_actual"] = "transferencias"
    state["tests_generados"] = {"transferencias": ["t1"]}
    state["iter_regresion"] = {"transferencias": 0}
    out = ejecutar_tests(state)
    assert out["resultado_tests"]["transferencias"]["ok"] is False


def test_ejecutar_tests_recupera_tras_regresion_p002():
    state = _base("P-002")
    state["lote_actual"] = "transferencias"
    state["tests_generados"] = {"transferencias": ["t1"]}
    state["iter_regresion"] = {"transferencias": 1}
    out = ejecutar_tests(state)
    assert out["resultado_tests"]["transferencias"]["ok"] is True
    assert out["resultado_tests"]["transferencias"]["detalle"] == "fix_post_regresion"


# Routers ---------------------------------------------------------------

def test_resultado_tests_router_ok_va_a_progreso():
    state = _base()
    state["lote_actual"] = "auth"
    state["resultado_tests"] = {"auth": {"ok": True}}
    assert resultado_tests_router(state) == "registrar_progreso"


def test_resultado_tests_router_falla_con_iter_disponible():
    state = _base()
    state["lote_actual"] = "auth"
    state["resultado_tests"] = {"auth": {"ok": False}}
    state["iter_regresion"] = {"auth": 0}
    assert resultado_tests_router(state) == "analizar_regresion"


def test_resultado_tests_router_falla_topa_iteraciones():
    state = _base()
    state["lote_actual"] = "auth"
    state["resultado_tests"] = {"auth": {"ok": False}}
    state["iter_regresion"] = {"auth": 99}
    assert resultado_tests_router(state) == "registrar_progreso"


def test_migracion_completa_router_pendientes():
    state = _base()
    state["lotes_pendientes"] = ["x"]
    assert migracion_completa_router(state) == "seleccionar_lote"


def test_migracion_completa_router_vacio():
    state = _base()
    state["lotes_pendientes"] = []
    assert migracion_completa_router(state) == "validacion_integral"


# Flujos end-to-end -----------------------------------------------------

def test_e2e_p001_exitosa():
    g = compile_graph()
    out = g.invoke(_base("P-001"), config={"configurable": {"thread_id": "t-p001"}})
    assert out["done"] is True
    assert out["estado_final"] == "exitosa"
    assert out["metricas"]["lotes_totales"] == 4
    assert out["metricas"]["lotes_workaround"] == 0
    assert out["metricas"]["regresiones_totales"] == 0


def test_e2e_p002_con_loop_regresion():
    g = compile_graph()
    out = g.invoke(_base("P-002"), config={"configurable": {"thread_id": "t-p002"}})
    assert out["done"] is True
    assert out["estado_final"] == "exitosa"
    assert out["metricas"]["regresiones_totales"] >= 1
    assert out["metricas"]["lotes_workaround"] == 0


def test_e2e_p003_parcial_workaround():
    g = compile_graph()
    out = g.invoke(_base("P-003"), config={"configurable": {"thread_id": "t-p003"}})
    assert out["done"] is True
    assert out["estado_final"] == "parcial"
    assert out["metricas"]["lotes_workaround"] >= 1


def test_e2e_eventos_p001():
    g = compile_graph()
    out = g.invoke(_base("P-001"), config={"configurable": {"thread_id": "t-events"}})
    types = [e["type"] for e in out["events"]]
    for esperado in [
        "codigo_analizado", "dependencias_mapeadas", "plan_generado",
        "lote_seleccionado", "modulo_refactorizado", "tests_generados",
        "tests_ejecutados", "progreso_registrado", "migracion_completada",
    ]:
        assert esperado in types, f"falta evento {esperado}"


def test_e2e_determinismo_p001():
    g1 = compile_graph()
    g2 = compile_graph()
    o1 = g1.invoke(_base("P-001"), config={"configurable": {"thread_id": "t-det-1"}})
    o2 = g2.invoke(_base("P-001"), config={"configurable": {"thread_id": "t-det-2"}})
    assert o1["estado_final"] == o2["estado_final"]
    assert o1["metricas"]["lotes_totales"] == o2["metricas"]["lotes_totales"]
    assert [p["modulo"] for p in o1["plan_migracion"]] == \
           [p["modulo"] for p in o2["plan_migracion"]]
