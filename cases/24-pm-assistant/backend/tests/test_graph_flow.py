"""Tests del grafo LangGraph — Caso 24: Asistente PM."""
import re

from src.graph import (
    PMState,
    asignar_sprint,
    clarificar_problema,
    compile_graph,
    crear_tickets,
    definir_epica,
    descomponer_historias,
    estado_sprint_router,
    estimar_complejidad,
    monitorear_progreso,
    priorizar_backlog,
)


def _base(iniciativa_id: str = "I-001") -> PMState:
    return {
        "iniciativa_id": iniciativa_id, "iniciativa": {},
        "preguntas_clarificadoras": [], "respuestas_clarificadoras": [],
        "epica": {}, "historias": [], "estimaciones": {},
        "backlog_priorizado": [], "tickets_creados": [],
        "sprint_asignado": {}, "progreso_sprint": {},
        "impedimentos": [], "estado_sprint": "", "reporte": "",
        "retrospectiva": {}, "estado_final": "", "metricas": {},
        "audit_trail": [], "events": [], "done": False,
    }


def _hydrate_until(state: PMState, *nodes) -> PMState:
    """Aplica una serie de nodos secuencialmente al state."""
    for node in nodes:
        out = node(state)
        for k, v in out.items():
            if k in ("events", "audit_trail"):
                state[k] = state.get(k, []) + v  # type: ignore[assignment]
            else:
                state[k] = v
    return state


def test_graph_compiles():
    assert compile_graph() is not None


# Nodos individuales

def test_clarificar_problema_i001():
    out = clarificar_problema(_base("I-001"))
    assert out["iniciativa"]["titulo"] == "Login con Google"
    assert len(out["preguntas_clarificadoras"]) == 3


def test_clarificar_problema_feedback():
    out = clarificar_problema(_base("I-004"))
    assert out["iniciativa"]["fuente"] == "feedback"
    assert len(out["preguntas_clarificadoras"]) == 3


def test_definir_epica():
    state = _hydrate_until(_base("I-001"), clarificar_problema, definir_epica)
    assert state["epica"]["id"] == "EP-001"
    assert len(state["epica"]["criterios_aceptacion"]) >= 1
    assert state["epica"]["metricas_exito"]


def test_descomponer_historias_formato():
    state = _hydrate_until(
        _base("I-001"), clarificar_problema, definir_epica, descomponer_historias,
    )
    assert len(state["historias"]) == 3
    for h in state["historias"]:
        # Formato: "Como X quiero Y para Z"
        assert re.match(r"^Como .+ quiero .+ para .+$", h["texto"])


def test_estimar_complejidad():
    state = _hydrate_until(
        _base("I-002"), clarificar_problema, definir_epica,
        descomponer_historias, estimar_complejidad,
    )
    # I-002 tiene XL=13 + M=5
    assert sum(state["estimaciones"].values()) == 18


def test_priorizar_backlog_orden():
    state = _hydrate_until(
        _base("I-004"), clarificar_problema, definir_epica,
        descomponer_historias, estimar_complejidad, priorizar_backlog,
    )
    backlog = state["backlog_priorizado"]
    # Ordenado por puntos asc (mismo valor_negocio)
    puntos = [h["puntos"] for h in backlog]
    assert puntos == sorted(puntos)


def test_crear_tickets_determinista():
    state1 = _hydrate_until(
        _base("I-001"), clarificar_problema, definir_epica,
        descomponer_historias, estimar_complejidad, priorizar_backlog, crear_tickets,
    )
    state2 = _hydrate_until(
        _base("I-001"), clarificar_problema, definir_epica,
        descomponer_historias, estimar_complejidad, priorizar_backlog, crear_tickets,
    )
    ids1 = [t["id"] for t in state1["tickets_creados"]]
    ids2 = [t["id"] for t in state2["tickets_creados"]]
    assert ids1 == ids2
    assert all(t["id"].startswith("PROJ-") for t in state1["tickets_creados"])


def test_asignar_sprint_respeta_capacidad():
    state = _hydrate_until(
        _base("I-004"), clarificar_problema, definir_epica,
        descomponer_historias, estimar_complejidad, priorizar_backlog,
        crear_tickets, asignar_sprint,
    )
    sprint = state["sprint_asignado"]
    # Capacidad min(policy=15, equipo EQ-REPORTS=12) = 12
    assert sprint["puntos_asignados"] <= sprint["capacidad"]
    # I-004 tiene 4 historias (5+8+5+8=26) en cap 12 → algunas fuera
    assert len(sprint["fuera_de_capacidad"]) >= 1


def test_asignar_sprint_i001_todo_cabe():
    state = _hydrate_until(
        _base("I-001"), clarificar_problema, definir_epica,
        descomponer_historias, estimar_complejidad, priorizar_backlog,
        crear_tickets, asignar_sprint,
    )
    sprint = state["sprint_asignado"]
    assert sprint["fuera_de_capacidad"] == []


def test_monitorear_progreso_normal():
    state = _hydrate_until(
        _base("I-001"), clarificar_problema, definir_epica,
        descomponer_historias, estimar_complejidad, priorizar_backlog,
        crear_tickets, asignar_sprint, monitorear_progreso,
    )
    assert state["estado_sprint"] == "normal"


# Routers

def test_router_normal():
    state = _base()
    state["estado_sprint"] = "normal"
    assert estado_sprint_router(state) == "generar_reporte_estado"


def test_router_impedimento():
    state = _base()
    state["estado_sprint"] = "impedimento"
    assert estado_sprint_router(state) == "escalar_impedimento"


def test_router_completado():
    state = _base()
    state["estado_sprint"] = "completado"
    assert estado_sprint_router(state) == "retrospectiva_y_metricas"


# Flujos end-to-end

def test_e2e_i001_normal():
    g = compile_graph()
    out = g.invoke(_base("I-001"), config={"configurable": {"thread_id": "t-i001"}})
    assert out["done"] is True
    assert out["estado_sprint"] == "normal"
    assert out["estado_final"] == "sprint_en_curso"
    assert out["retrospectiva"] == {}


def test_e2e_i002_impedimento():
    g = compile_graph()
    out = g.invoke(_base("I-002"), config={"configurable": {"thread_id": "t-i002"}})
    assert out["estado_sprint"] == "impedimento"
    assert out["estado_final"] == "sprint_con_impedimento"
    types = [e["type"] for e in out["events"]]
    assert "impedimento_escalado" in types


def test_e2e_i003_completado():
    g = compile_graph()
    out = g.invoke(_base("I-003"), config={"configurable": {"thread_id": "t-i003"}})
    assert out["estado_sprint"] == "completado"
    assert out["estado_final"] == "sprint_completado"
    assert out["retrospectiva"]["predictibilidad"] >= 0.99
    types = [e["type"] for e in out["events"]]
    assert "retrospectiva_calculada" in types


def test_e2e_i004_fuera_de_capacidad():
    g = compile_graph()
    out = g.invoke(_base("I-004"), config={"configurable": {"thread_id": "t-i004"}})
    assert out["estado_sprint"] == "normal"
    assert len(out["sprint_asignado"]["fuera_de_capacidad"]) >= 1


def test_formato_historia_regex_e2e():
    g = compile_graph()
    out = g.invoke(_base("I-001"), config={"configurable": {"thread_id": "t-fmt"}})
    pattern = re.compile(r"^Como .+ quiero .+ para .+$")
    assert all(pattern.match(h["texto"]) for h in out["historias"])


def test_determinismo_tickets_e2e():
    g1 = compile_graph()
    g2 = compile_graph()
    o1 = g1.invoke(_base("I-001"), config={"configurable": {"thread_id": "t-det-1"}})
    o2 = g2.invoke(_base("I-001"), config={"configurable": {"thread_id": "t-det-2"}})
    ids1 = [t["id"] for t in o1["tickets_creados"]]
    ids2 = [t["id"] for t in o2["tickets_creados"]]
    assert ids1 == ids2
