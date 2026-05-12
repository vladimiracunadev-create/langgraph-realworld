"""Tests del grafo LangGraph — Caso 11: Tutor Adaptativo."""
import random

from src.graph import (
    TutorState,
    _clamp,
    _simulate_response,
    compile_graph,
    continuar_router,
    desempeno_router,
    diagnostico_router,
)


def _base(student_id: str = "STU-002") -> TutorState:
    return {
        "student_id": student_id,
        "student": {}, "policy": {},
        "diagnostico_aplicado": False,
        "habilidad": 0.0, "habilidad_inicial": 0.0,
        "max_items": 0,
        "items_disponibles": [], "items_servidos": [],
        "current_item": {}, "evaluacion_actual": {},
        "evaluaciones": [],
        "conceptos_dominados": [], "conceptos_a_remediar": [],
        "errores_consecutivos": 0, "ajuste_ultimo": "",
        "perfil_final": {}, "reporte": "",
        "events": [], "done": False,
    }


# ---------------------------------------------------------------------------
# Compilación + helpers puros
# ---------------------------------------------------------------------------

def test_graph_compiles():
    assert compile_graph() is not None


def test_clamp():
    assert _clamp(5, 1, 10) == 5
    assert _clamp(-1, 1, 10) == 1
    assert _clamp(99, 1, 10) == 10


def test_simulate_correcto_si_item_facil():
    item = {"id": "X", "concepto": "c", "dificultad": 2.0, "respuesta_correcta": "ok"}
    policy = {"tolerancia_dominio": 0.5, "umbral_error_conceptual": 2.0,
              "umbral_frustracion": 3.5, "errores_consecutivos_frustracion": 2}
    ev = _simulate_response(item, habilidad=6.0, policy=policy,
                            errores_consecutivos=0, rng=random.Random(1))
    assert ev["resultado"] == "correcto"


def test_simulate_frustracion_si_item_muy_dificil():
    item = {"id": "X", "concepto": "c", "dificultad": 9.0, "respuesta_correcta": "ok"}
    policy = {"tolerancia_dominio": 0.5, "umbral_error_conceptual": 2.0,
              "umbral_frustracion": 3.5, "errores_consecutivos_frustracion": 2}
    ev = _simulate_response(item, habilidad=2.5, policy=policy,
                            errores_consecutivos=0, rng=random.Random(1))
    assert ev["resultado"] == "frustracion"


def test_simulate_error_conceptual_en_zona_media():
    item = {"id": "X", "concepto": "c", "dificultad": 6.5, "respuesta_correcta": "ok"}
    policy = {"tolerancia_dominio": 0.5, "umbral_error_conceptual": 2.0,
              "umbral_frustracion": 3.5, "errores_consecutivos_frustracion": 2}
    ev = _simulate_response(item, habilidad=4.0, policy=policy,
                            errores_consecutivos=0, rng=random.Random(1))
    assert ev["resultado"] == "error_conceptual"


def test_simulate_frustracion_por_racha():
    item = {"id": "X", "concepto": "c", "dificultad": 5.0, "respuesta_correcta": "ok"}
    policy = {"tolerancia_dominio": 0.5, "umbral_error_conceptual": 2.0,
              "umbral_frustracion": 3.5, "errores_consecutivos_frustracion": 2}
    ev = _simulate_response(item, habilidad=3.5, policy=policy,
                            errores_consecutivos=3, rng=random.Random(1))
    assert ev["resultado"] == "frustracion"


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

def test_diagnostico_router_sin():
    state = _base()
    state["diagnostico_aplicado"] = False
    assert diagnostico_router(state) == "sin_diagnostico"


def test_diagnostico_router_con():
    state = _base()
    state["diagnostico_aplicado"] = True
    assert diagnostico_router(state) == "con_diagnostico"


def test_desempeno_router_tres_vias():
    state = _base()
    state["evaluacion_actual"] = {"resultado": "correcto"}
    assert desempeno_router(state) == "domina"
    state["evaluacion_actual"] = {"resultado": "error_conceptual"}
    assert desempeno_router(state) == "error_conceptual"
    state["evaluacion_actual"] = {"resultado": "frustracion"}
    assert desempeno_router(state) == "frustracion"


def test_continuar_router_finaliza_por_max():
    state = _base()
    state["max_items"] = 6
    state["items_servidos"] = ["a", "b", "c", "d", "e", "f"]
    state["items_disponibles"] = list(range(10))
    assert continuar_router(state) == "finalizar"


def test_continuar_router_continua():
    state = _base()
    state["max_items"] = 6
    state["items_servidos"] = ["a", "b"]
    state["items_disponibles"] = list(range(10))
    assert continuar_router(state) == "continuar"


# ---------------------------------------------------------------------------
# Flujos end-to-end por estudiante
# ---------------------------------------------------------------------------

def test_e2e_stu001_sin_diagnostico_se_aplica():
    """STU-001 sin habilidad_inicial → aplica diagnóstico antes del loop."""
    g = compile_graph()
    out = g.invoke(_base("STU-001"), config={"configurable": {"thread_id": "t-001"}})
    assert out["done"] is True
    types = [e["type"] for e in out["events"]]
    assert "diagnostico_aplicado" in types
    assert out["perfil_final"]["items_resueltos"] >= 1


def test_e2e_stu002_con_diagnostico_omite_pretest():
    """STU-002 viene con habilidad_inicial=5.5 → no aplica diagnóstico."""
    g = compile_graph()
    out = g.invoke(_base("STU-002"), config={"configurable": {"thread_id": "t-002"}})
    assert out["done"] is True
    types = [e["type"] for e in out["events"]]
    assert "diagnostico_aplicado" not in types
    assert out["habilidad_inicial"] == 5.5


def test_e2e_stu003_nivel_bajo_genera_remediacion_o_reduccion():
    """STU-003 nivel bajo (2.5) → genera al menos un evento de remediación o reducción."""
    g = compile_graph()
    out = g.invoke(_base("STU-003"), config={"configurable": {"thread_id": "t-003"}})
    assert out["done"] is True
    types = [e["type"] for e in out["events"]]
    assert "concepto_remediado" in types or "dificultad_reducida" in types


def test_e2e_max_items_respetado():
    g = compile_graph()
    out = g.invoke(_base("STU-002"), config={"configurable": {"thread_id": "t-max"}})
    assert len(out["evaluaciones"]) <= out["max_items"]
    assert len(out["items_servidos"]) == len(out["evaluaciones"])


def test_e2e_items_no_repetidos():
    g = compile_graph()
    out = g.invoke(_base("STU-002"), config={"configurable": {"thread_id": "t-norep"}})
    assert len(out["items_servidos"]) == len(set(out["items_servidos"]))


def test_e2e_perfil_metricas_consistentes():
    g = compile_graph()
    out = g.invoke(_base("STU-002"), config={"configurable": {"thread_id": "t-met"}})
    perfil = out["perfil_final"]
    total = perfil["items_resueltos"]
    suma = perfil["aciertos"] + perfil["errores_conceptuales"] + perfil["frustraciones"]
    assert suma == total
    assert 0.0 <= perfil["tasa_acierto"] <= 1.0


def test_e2e_reporte_no_vacio():
    g = compile_graph()
    out = g.invoke(_base("STU-001"), config={"configurable": {"thread_id": "t-rep"}})
    assert out["reporte"]
    assert "Reporte" in out["reporte"]


def test_e2e_eventos_pipeline_completos():
    g = compile_graph()
    out = g.invoke(_base("STU-002"), config={"configurable": {"thread_id": "t-evs"}})
    types = [e["type"] for e in out["events"]]
    for expected in [
        "perfil_cargado",
        "item_seleccionado",
        "actividad_presentada",
        "respuesta_evaluada",
        "perfil_actualizado",
        "sesion_completada",
    ]:
        assert expected in types, f"falta evento {expected}"


def test_e2e_habilidad_acotada():
    g = compile_graph()
    out = g.invoke(_base("STU-003"), config={"configurable": {"thread_id": "t-bound"}})
    assert 1.0 <= out["habilidad"] <= 10.0
