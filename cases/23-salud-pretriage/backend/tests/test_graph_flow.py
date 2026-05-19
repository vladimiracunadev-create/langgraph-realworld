"""Tests del grafo LangGraph — Caso 23: Salud Pre-triage Administrativo."""
import re

from src.graph import (
    DISCLAIMER_DEFAULT,
    PretriageState,
    bienvenida_y_datos_basicos,
    clasificar_nivel_urgencia,
    compile_graph,
    nivel_urgencia_router,
    preguntar_sintomas_referidos,
    recopilar_antecedentes_relevantes,
    recopilar_motivo_consulta,
    verificar_cobertura_documentacion,
)


def _base(sesion_id: str = "S-001") -> PretriageState:
    return {
        "sesion_id": sesion_id, "paciente": {}, "motivo_consulta": "",
        "sintomas": [], "antecedentes": {}, "cobertura_ok": False,
        "documentacion_faltante": [], "nivel_urgencia": "", "puntaje_urgencia": 0,
        "derivacion": {}, "resumen_derivacion": "", "disclaimer": "",
        "estado_final": "", "audit_trail": [], "metricas": {},
        "events": [], "done": False,
    }


def test_graph_compiles():
    assert compile_graph() is not None


# Nodos individuales

def test_bienvenida_carga_paciente():
    out = bienvenida_y_datos_basicos(_base("S-001"))
    assert out["paciente"]["nombre"] == "María González"
    assert out["paciente"]["edad"] == 55
    # Disclaimer cargado desde policy
    assert "administrativa" in out["disclaimer"].lower()


def test_recopilar_motivo_s002():
    out = recopilar_motivo_consulta(_base("S-002"))
    assert "lumbalgia" in out["motivo_consulta"].lower()


def test_preguntar_sintomas_s001():
    out = preguntar_sintomas_referidos(_base("S-001"))
    assert "dolor_toracico" in out["sintomas"]


def test_recopilar_antecedentes_s001():
    out = recopilar_antecedentes_relevantes(_base("S-001"))
    assert "hipertension" in out["antecedentes"]["comorbilidades"]


def test_verificar_cobertura_ok_s001():
    state = _base("S-001")
    bw = bienvenida_y_datos_basicos(state)
    state["paciente"] = bw["paciente"]
    out = verificar_cobertura_documentacion(state)
    assert out["cobertura_ok"] is True
    assert out["documentacion_faltante"] == []


def test_verificar_cobertura_faltante_s004():
    state = _base("S-004")
    bw = bienvenida_y_datos_basicos(state)
    state["paciente"] = bw["paciente"]
    out = verificar_cobertura_documentacion(state)
    assert out["cobertura_ok"] is False
    assert "credencial_cobertura" in out["documentacion_faltante"]


def test_clasificar_s001_inmediata():
    """S-001: dolor_torácico + edad 55 + comorbilidad → puntaje >= 70."""
    state = _base("S-001")
    state["cobertura_ok"] = True
    state["paciente"] = {"edad": 55}
    state["motivo_consulta"] = "dolor torácico agudo"
    state["sintomas"] = ["dolor_toracico", "sudoracion", "irradiacion_brazo_izq"]
    state["antecedentes"] = {"comorbilidades": ["hipertension"]}
    out = clasificar_nivel_urgencia(state)
    assert out["nivel_urgencia"] == "inmediata"
    assert out["puntaje_urgencia"] >= 70


def test_clasificar_s003_teleconsulta_por_motivo_control():
    state = _base("S-003")
    state["cobertura_ok"] = True
    state["paciente"] = {"edad": 35}
    state["motivo_consulta"] = "consulta de control por hipertensión estable"
    state["sintomas"] = []
    state["antecedentes"] = {"comorbilidades": ["hipertension"]}
    out = clasificar_nivel_urgencia(state)
    assert out["nivel_urgencia"] == "teleconsulta"


def test_clasificar_cobertura_pendiente():
    state = _base("S-004")
    state["cobertura_ok"] = False
    out = clasificar_nivel_urgencia(state)
    assert out["nivel_urgencia"] == "cobertura_pendiente"
    assert out["puntaje_urgencia"] == 0


# Router — 4 ramas

def test_router_inmediata():
    state = _base()
    state["nivel_urgencia"] = "inmediata"
    assert nivel_urgencia_router(state) == "derivar_urgencias"


def test_router_programable():
    state = _base()
    state["nivel_urgencia"] = "programable"
    assert nivel_urgencia_router(state) == "derivar_especialidad"


def test_router_teleconsulta():
    state = _base()
    state["nivel_urgencia"] = "teleconsulta"
    assert nivel_urgencia_router(state) == "derivar_teleconsulta"


def test_router_cobertura_pendiente():
    state = _base()
    state["nivel_urgencia"] = "cobertura_pendiente"
    assert nivel_urgencia_router(state) == "derivar_documentacion_pendiente"


# Flujos end-to-end

def test_e2e_s001_urgencias():
    g = compile_graph()
    out = g.invoke(_base("S-001"), config={"configurable": {"thread_id": "t-e2e-s001"}})
    assert out["done"] is True
    assert out["nivel_urgencia"] == "inmediata"
    assert out["estado_final"] == "derivado_urgencias"
    assert out["derivacion"]["servicio"] == "urgencias"


def test_e2e_s002_programable_traumatologia():
    g = compile_graph()
    out = g.invoke(_base("S-002"), config={"configurable": {"thread_id": "t-e2e-s002"}})
    assert out["nivel_urgencia"] == "programable"
    assert out["derivacion"]["servicio"] == "traumatologia"


def test_e2e_s003_teleconsulta():
    g = compile_graph()
    out = g.invoke(_base("S-003"), config={"configurable": {"thread_id": "t-e2e-s003"}})
    assert out["nivel_urgencia"] == "teleconsulta"
    assert out["derivacion"]["modalidad"] == "telemedicina"


def test_e2e_s004_documentacion_pendiente():
    g = compile_graph()
    out = g.invoke(_base("S-004"), config={"configurable": {"thread_id": "t-e2e-s004"}})
    assert out["cobertura_ok"] is False
    assert out["estado_final"] == "derivado_documentacion_pendiente"
    assert out["derivacion"]["servicio"] == "admision_documentacion"


def test_disclaimer_presente_en_resumen():
    """Cada output al paciente debe incluir el disclaimer obligatorio."""
    g = compile_graph()
    for sid in ("S-001", "S-002", "S-003", "S-004"):
        out = g.invoke(_base(sid), config={"configurable": {"thread_id": f"t-disc-{sid}"}})
        assert out["disclaimer"], f"sin disclaimer en {sid}"
        assert out["disclaimer"] in out["resumen_derivacion"], (
            f"disclaimer no embebido en resumen de {sid}"
        )


def test_no_emite_lenguaje_de_diagnostico_medico():
    """
    REGULATORIO: el agente NO emite diagnóstico ni indicación médica.
    Las palabras 'diagnóstico' o 'indicación médica' sólo pueden aparecer
    en contexto de la negación explícita (el disclaimer).
    """
    g = compile_graph()
    palabras_prohibidas = [
        r"\bdiagn[oó]stico\b",
        r"\bindicaci[oó]n m[eé]dica\b",
        r"\bprescrib[oe]\b",
        r"\bdiagnostic[ao]\b",
    ]
    for sid in ("S-001", "S-002", "S-003", "S-004"):
        out = g.invoke(_base(sid), config={"configurable": {"thread_id": f"t-noDx-{sid}"}})
        resumen = out["resumen_derivacion"]
        disclaimer = out["disclaimer"]
        # Quita el disclaimer y revisa el resto del resumen
        cuerpo = resumen.replace(disclaimer, "")
        # También quita la línea "NO emite diagnóstico..." si aparece
        cuerpo_low = cuerpo.lower()
        for patron in palabras_prohibidas:
            assert not re.search(patron, cuerpo_low), (
                f"Sesión {sid}: lenguaje diagnóstico fuera del disclaimer "
                f"(patrón {patron}). Cuerpo:\n{cuerpo}"
            )


def test_clasificacion_es_determinista():
    """Mismo input → misma clasificación administrativa."""
    g1 = compile_graph()
    g2 = compile_graph()
    o1 = g1.invoke(_base("S-001"), config={"configurable": {"thread_id": "t-det-1"}})
    o2 = g2.invoke(_base("S-001"), config={"configurable": {"thread_id": "t-det-2"}})
    assert o1["nivel_urgencia"] == o2["nivel_urgencia"]
    assert o1["puntaje_urgencia"] == o2["puntaje_urgencia"]
    assert o1["derivacion"]["servicio"] == o2["derivacion"]["servicio"]


def test_disclaimer_default_constante_no_diagnostico():
    assert "diagnóstico" in DISCLAIMER_DEFAULT.lower()
    assert "administrativa" in DISCLAIMER_DEFAULT.lower()
