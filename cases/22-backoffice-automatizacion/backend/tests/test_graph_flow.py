"""Tests del grafo LangGraph — Caso 22: Backoffice."""
from src.graph import (
    BackofficeState,
    _hash_eslabon,
    clasificar_tipo_operacion,
    compile_graph,
    completitud_router,
    ejecucion_router,
    parsear_solicitud,
    permisos_router,
    verificar_identidad,
)


def _base(solicitud_id: str = "SOL-001") -> BackofficeState:
    return {
        "solicitud_id": solicitud_id, "solicitud": {}, "operacion": {},
        "solicitante": {}, "permisos_ok": False, "motivo_rechazo": "",
        "datos_completos": False, "campos_faltantes": [], "iter_completitud": 0,
        "resultado_ejecucion": {}, "estado_final": "", "confirmacion": "",
        "log_auditoria": [], "hash_auditoria": "", "resumen": "",
        "metricas": {}, "events": [], "done": False,
    }


def test_graph_compiles():
    assert compile_graph() is not None


# Helpers

def test_hash_eslabon_cambia_con_payload():
    a = _hash_eslabon("0" * 64, {"x": 1})
    b = _hash_eslabon("0" * 64, {"x": 2})
    assert a != b
    assert len(a) == 64


def test_hash_eslabon_encadena():
    a = _hash_eslabon("0" * 64, {"x": 1})
    b = _hash_eslabon(a, {"x": 1})
    assert a != b


# Nodos

def test_parsear_sol001():
    out = parsear_solicitud(_base("SOL-001"))
    assert out["solicitud"]["tipo_operacion"] == "alta_usuario_crm"
    assert out["iter_completitud"] == 0
    assert out["hash_auditoria"] == "0" * 64


def test_clasificar_operacion_conocida():
    state = _base("SOL-001")
    state["solicitud"] = parsear_solicitud(state)["solicitud"]
    out = clasificar_tipo_operacion(state)
    assert out["operacion"]["conocida"] is True
    assert out["operacion"]["sistema"] == "CRM"
    assert "nombre_completo" in out["operacion"]["campos_requeridos"]


def test_verificar_identidad_sol001_ok():
    state = _base("SOL-001")
    state["solicitud"] = parsear_solicitud(state)["solicitud"]
    state["operacion"] = clasificar_tipo_operacion(state)["operacion"]
    out = verificar_identidad(state)
    assert out["permisos_ok"] is True
    assert out["motivo_rechazo"] == ""


def test_verificar_identidad_sol003_sin_permiso():
    state = _base("SOL-003")
    state["solicitud"] = parsear_solicitud(state)["solicitud"]
    state["operacion"] = clasificar_tipo_operacion(state)["operacion"]
    out = verificar_identidad(state)
    assert out["permisos_ok"] is False
    assert out["motivo_rechazo"] == "sin_permiso_para_operacion"


# Routers

def test_permisos_router_aprueba():
    state = _base()
    state["permisos_ok"] = True
    assert permisos_router(state) == "validar_datos_operacion"


def test_permisos_router_rechaza():
    state = _base()
    state["permisos_ok"] = False
    assert permisos_router(state) == "rechazar_solicitud"


def test_completitud_router_loop():
    state = _base()
    state["datos_completos"] = False
    state["iter_completitud"] = 0
    assert completitud_router(state) == "solicitar_informacion"


def test_completitud_router_avanza_si_completos():
    state = _base()
    state["datos_completos"] = True
    assert completitud_router(state) == "ejecutar_operacion"


def test_completitud_router_avanza_si_tope():
    state = _base()
    state["datos_completos"] = False
    state["iter_completitud"] = 5
    assert completitud_router(state) == "ejecutar_operacion"


def test_ejecucion_router_exito():
    state = _base()
    state["resultado_ejecucion"] = {"ok": True}
    assert ejecucion_router(state) == "confirmar_solicitante"


def test_ejecucion_router_fallo():
    state = _base()
    state["resultado_ejecucion"] = {"ok": False}
    assert ejecucion_router(state) == "escalar_soporte"


# Flujos end-to-end

def test_e2e_sol001_exitosa():
    g = compile_graph()
    out = g.invoke(_base("SOL-001"), config={"configurable": {"thread_id": "t-sol001"}})
    assert out["done"] is True
    assert out["estado_final"] == "exitosa"
    assert out["iter_completitud"] == 0
    assert out["resultado_ejecucion"]["ok"] is True
    assert "referencia" in out["resultado_ejecucion"]


def test_e2e_sol002_loop_completitud():
    g = compile_graph()
    out = g.invoke(_base("SOL-002"), config={"configurable": {"thread_id": "t-sol002"}})
    assert out["done"] is True
    assert out["iter_completitud"] >= 1
    assert out["estado_final"] == "exitosa"


def test_e2e_sol003_rechazada():
    g = compile_graph()
    out = g.invoke(_base("SOL-003"), config={"configurable": {"thread_id": "t-sol003"}})
    assert out["done"] is True
    assert out["estado_final"] == "rechazada"
    # No debe llegar a ejecutar
    assert out["resultado_ejecucion"] == {}


def test_e2e_sol004_escalada():
    g = compile_graph()
    out = g.invoke(_base("SOL-004"), config={"configurable": {"thread_id": "t-sol004"}})
    assert out["estado_final"] == "escalada"
    assert out["resultado_ejecucion"]["ok"] is False


def test_eventos_completos_sol001():
    g = compile_graph()
    out = g.invoke(_base("SOL-001"), config={"configurable": {"thread_id": "t-events"}})
    types = [e["type"] for e in out["events"]]
    for esperado in [
        "solicitud_parseada", "operacion_clasificada", "identidad_verificada",
        "datos_validados", "operacion_ejecutada", "solicitante_confirmado",
        "log_registrado", "backoffice_completado",
    ]:
        assert esperado in types, f"falta evento {esperado}"


def test_log_auditoria_inmutable_sol001():
    g = compile_graph()
    out = g.invoke(_base("SOL-001"), config={"configurable": {"thread_id": "t-audit"}})
    log = out["log_auditoria"]
    assert len(log) >= 5
    prev = "0" * 64
    for eslabon in log:
        assert eslabon["prev_hash"] == prev
        prev = eslabon["hash"]
    assert out["hash_auditoria"] == prev


def test_referencia_es_determinista():
    """Mismo input → misma referencia (no depende de PYTHONHASHSEED)."""
    g1 = compile_graph()
    g2 = compile_graph()
    o1 = g1.invoke(_base("SOL-001"), config={"configurable": {"thread_id": "t-det-1"}})
    o2 = g2.invoke(_base("SOL-001"), config={"configurable": {"thread_id": "t-det-2"}})
    assert o1["resultado_ejecucion"]["referencia"] == o2["resultado_ejecucion"]["referencia"]
