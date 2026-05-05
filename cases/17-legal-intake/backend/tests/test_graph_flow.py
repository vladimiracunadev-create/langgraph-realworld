"""Tests del grafo LangGraph — Caso 17: Legal Intake."""
from src.graph import (
    IntakeState,
    clasificar_tipo_caso,
    compile_graph,
    recibir_solicitud,
    route_by_completitud,
    route_by_especialidad,
    validar_informacion,
)


def _base_state(intake_id: str = "INT-001") -> IntakeState:
    return {
        "intake_id": intake_id,
        "cliente_nombre": "",
        "cliente_contacto": "",
        "asunto_libre": "",
        "documentos_aportados": [],
        "tipo_caso": "",
        "subtipo": "",
        "hechos": {},
        "campos_requeridos": [],
        "campos_faltantes": [],
        "preguntas_pendientes": [],
        "completitud": "",
        "urgencia": "",
        "plazo_critico": "",
        "razon_urgencia": "",
        "documento_tipo": "",
        "documento_borrador": "",
        "abogado_asignado": {},
        "resumen_intake": "",
        "events": [],
        "done": False,
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def test_graph_compiles():
    assert compile_graph() is not None


# ---------------------------------------------------------------------------
# Nodo: recibir_solicitud
# ---------------------------------------------------------------------------

def test_recibir_solicitud_int001():
    out = recibir_solicitud(_base_state("INT-001"))
    assert out["cliente_nombre"]
    assert out["asunto_libre"]
    assert out["events"][0]["type"] == "solicitud_recibida"


def test_recibir_solicitud_fallback():
    out = recibir_solicitud(_base_state("INT-NONEXISTENT"))
    assert out["cliente_nombre"]


# ---------------------------------------------------------------------------
# Nodo: clasificar_tipo_caso
# ---------------------------------------------------------------------------

def test_clasificar_laboral():
    state = _base_state()
    state["asunto_libre"] = (
        "Me despidieron invocando el artículo 161 del código del trabajo, "
        "tengo contrato de trabajo y liquidaciones de sueldo."
    )
    out = clasificar_tipo_caso(state)
    assert out["tipo_caso"] == "laboral"
    assert out["subtipo"] == "despido_injustificado"


def test_clasificar_mercantil():
    state = _base_state()
    state["asunto_libre"] = (
        "Contrato de suministro firmado con cláusula penal del 5%. "
        "Incumplimiento de SLA y necesitamos requerimiento extrajudicial."
    )
    out = clasificar_tipo_caso(state)
    assert out["tipo_caso"] == "mercantil"
    assert out["subtipo"] == "incumplimiento_contractual"


def test_clasificar_civil():
    state = _base_state()
    state["asunto_libre"] = (
        "Mi padre falleció sin testamento. Somos tres hermanos y queremos "
        "regularizar la sucesión y la posesión efectiva."
    )
    out = clasificar_tipo_caso(state)
    assert out["tipo_caso"] == "civil"
    assert out["subtipo"] == "sucesion_intestada"


# ---------------------------------------------------------------------------
# Nodo: validar_informacion
# ---------------------------------------------------------------------------

def test_validar_completa_cuando_todo_presente():
    state = _base_state()
    state["subtipo"] = "despido_injustificado"
    state["hechos"] = {
        "fecha_inicio_contrato": "2021",
        "fecha_termino": "12 de abril de 2026",
        "causal_invocada": "artículo 161",
        "ultimo_sueldo_bruto": "$1.840.000",
        "documentos_clave": "según listado",
    }
    out = validar_informacion(state)
    assert out["completitud"] == "completa"
    assert out["campos_faltantes"] == []


def test_validar_faltante_cuando_falta_campo():
    state = _base_state()
    state["subtipo"] = "sucesion_intestada"
    state["hechos"] = {
        "fecha_fallecimiento": "",
        "certificado_defuncion": "",
        "herederos_identificados": "tres hermanos",
        "bienes_inventariados": "casa, departamento",
        "estado_civil_causante": "viudo/a",
    }
    out = validar_informacion(state)
    assert out["completitud"] == "faltante"
    assert "fecha_fallecimiento" in out["campos_faltantes"]
    assert "certificado_defuncion" in out["campos_faltantes"]
    assert len(out["preguntas_pendientes"]) >= 2


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

def test_route_especialidad_laboral():
    state = _base_state(); state["tipo_caso"] = "laboral"
    assert route_by_especialidad(state) == "recopilar_hechos_laboral"


def test_route_especialidad_mercantil():
    state = _base_state(); state["tipo_caso"] = "mercantil"
    assert route_by_especialidad(state) == "recopilar_hechos_mercantil"


def test_route_especialidad_civil_default():
    state = _base_state(); state["tipo_caso"] = "civil"
    assert route_by_especialidad(state) == "recopilar_hechos_civil"


def test_route_completitud_faltante():
    state = _base_state(); state["completitud"] = "faltante"
    assert route_by_completitud(state) == "solicitar_informacion_faltante"


def test_route_completitud_completa():
    state = _base_state(); state["completitud"] = "completa"
    assert route_by_completitud(state) == "evaluar_urgencia"


# ---------------------------------------------------------------------------
# Flujos end-to-end
# ---------------------------------------------------------------------------

def test_flujo_int001_laboral_alta_urgencia():
    """INT-001 debe terminar con tipo laboral, urgencia alta y borrador de demanda."""
    graph = compile_graph()
    cfg = {"configurable": {"thread_id": "test-e2e-int001"}, "recursion_limit": 50}
    out = graph.invoke(_base_state("INT-001"), config=cfg)

    assert out.get("done") is True
    assert out.get("tipo_caso") == "laboral"
    assert out.get("urgencia") == "alta"
    assert out.get("documento_tipo") == "demanda_laboral"
    assert out.get("documento_borrador", "") != ""
    assert out.get("abogado_asignado", {}).get("especialidad") == "laboral"


def test_flujo_int002_mercantil():
    """INT-002 debe terminar con tipo mercantil y requerimiento extrajudicial."""
    graph = compile_graph()
    cfg = {"configurable": {"thread_id": "test-e2e-int002"}, "recursion_limit": 50}
    out = graph.invoke(_base_state("INT-002"), config=cfg)

    assert out.get("done") is True
    assert out.get("tipo_caso") == "mercantil"
    assert out.get("documento_tipo") == "requerimiento_extrajudicial"
    assert out.get("abogado_asignado", {}).get("especialidad") == "mercantil"


def test_flujo_int003_civil_faltante():
    """INT-003 debe terminar con tipo civil, completitud faltante y placeholders pendientes."""
    graph = compile_graph()
    cfg = {"configurable": {"thread_id": "test-e2e-int003"}, "recursion_limit": 50}
    out = graph.invoke(_base_state("INT-003"), config=cfg)

    assert out.get("done") is True
    assert out.get("tipo_caso") == "civil"
    assert out.get("subtipo") == "sucesion_intestada"
    assert out.get("completitud") == "faltante"
    assert len(out.get("preguntas_pendientes", [])) > 0
    assert "{{PENDIENTE" in out.get("documento_borrador", "")


def test_flujo_eventos_auditados():
    """El flujo completo debe producir todos los eventos esperados."""
    graph = compile_graph()
    cfg = {"configurable": {"thread_id": "test-e2e-events"}, "recursion_limit": 50}
    out = graph.invoke(_base_state("INT-001"), config=cfg)

    types = [e["type"] for e in out.get("events", [])]
    for expected in [
        "solicitud_recibida",
        "entrevista_realizada",
        "caso_clasificado",
        "informacion_validada",
        "urgencia_evaluada",
        "borrador_generado",
        "abogado_asignado",
        "intake_completado",
    ]:
        assert expected in types, f"falta evento {expected} en {types}"
