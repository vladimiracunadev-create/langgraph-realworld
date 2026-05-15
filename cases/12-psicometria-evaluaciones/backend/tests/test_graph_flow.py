"""Tests del grafo LangGraph — Caso 12: Psicometría y Evaluaciones."""

from src.graph import (
    EvalState,
    alpha_cronbach,
    compile_graph,
    dif_entre_grupos,
    indice_dificultad,
    indice_discriminacion,
    validez_router,
)


def _base(instrument_id: str = "INST-COMP-DIG-01") -> EvalState:
    return {
        "instrument_id": instrument_id,
        "instrument": {}, "policy": {},
        "items_candidatos": [], "items_revisados": [],
        "items_rechazados_revision": [], "items_aprobados": [],
        "respuestas": [], "instrumento_actual": [],
        "psicometria": {}, "items_problematicos": [],
        "iteracion_validez": 0, "valido": False,
        "baremos": {}, "puntajes_individuales": [],
        "informe_grupal": {}, "reporte": "",
        "events": [], "done": False,
    }


# ---------------------------------------------------------------------------
# Compilación + helpers psicométricos puros
# ---------------------------------------------------------------------------

def test_graph_compiles():
    assert compile_graph() is not None


def test_alpha_perfectamente_consistente():
    # 4 evaluados, 3 ítems; aciertos crecientes y monotónicos → α alto
    matrix = [[1, 1, 1], [1, 1, 0], [1, 0, 0], [0, 0, 0]]
    a = alpha_cronbach(matrix)
    assert a > 0.7


def test_alpha_inconsistente_es_bajo():
    # respuestas casi azarosas → α bajo o negativo
    matrix = [[1, 0, 1], [0, 1, 0], [1, 0, 1], [0, 1, 0]]
    a = alpha_cronbach(matrix)
    assert a < 0.5


def test_indice_dificultad_dicotomico():
    assert indice_dificultad([1, 1, 0, 0], "dicotomico") == 0.5
    assert indice_dificultad([1, 1, 1, 1], "dicotomico") == 1.0


def test_indice_dificultad_likert():
    assert indice_dificultad([1, 2, 3, 4, 5], "likert") == 3.0


def test_indice_discriminacion_positivo():
    # ítem alineado con el total → discriminación positiva
    item = [1.0, 1.0, 0.0, 0.0]
    total = [3.0, 2.5, 1.0, 0.5]
    d = indice_discriminacion(item, total)
    assert d > 0.5


def test_indice_discriminacion_invertido_negativo():
    # ítem invertido respecto al total → discriminación negativa
    item = [0.0, 0.0, 1.0, 1.0]
    total = [3.0, 2.5, 1.0, 0.5]
    d = indice_discriminacion(item, total)
    assert d < 0


def test_dif_grupos_detecta_diferencia():
    resp = [
        {"evaluado_id": "E1", "grupo": "a", "respuestas": {"X": 1}},
        {"evaluado_id": "E2", "grupo": "a", "respuestas": {"X": 1}},
        {"evaluado_id": "E3", "grupo": "b", "respuestas": {"X": 0}},
        {"evaluado_id": "E4", "grupo": "b", "respuestas": {"X": 0}},
    ]
    assert dif_entre_grupos(resp, "X", ["a", "b"], "dicotomico") == 1.0


def test_dif_grupos_sin_diferencia():
    resp = [
        {"evaluado_id": "E1", "grupo": "a", "respuestas": {"X": 1}},
        {"evaluado_id": "E2", "grupo": "b", "respuestas": {"X": 1}},
    ]
    assert dif_entre_grupos(resp, "X", ["a", "b"], "dicotomico") == 0.0


# ---------------------------------------------------------------------------
# Router de validez
# ---------------------------------------------------------------------------

def test_validez_router_valido_si_alpha_alta():
    s = _base()
    s["instrument"] = {"umbral_alpha": 0.70}
    s["psicometria"] = {"alpha_cronbach": 0.85}
    s["policy"] = {"max_iteraciones_validez": 2}
    s["iteracion_validez"] = 1
    assert validez_router(s) == "valido"


def test_validez_router_revision_si_alpha_baja():
    s = _base()
    s["instrument"] = {"umbral_alpha": 0.70}
    s["psicometria"] = {"alpha_cronbach": 0.50}
    s["policy"] = {"max_iteraciones_validez": 2}
    s["iteracion_validez"] = 1
    assert validez_router(s) == "requiere_revision"


def test_validez_router_corta_al_alcanzar_tope():
    s = _base()
    s["instrument"] = {"umbral_alpha": 0.70}
    s["psicometria"] = {"alpha_cronbach": 0.40}
    s["policy"] = {"max_iteraciones_validez": 2}
    s["iteracion_validez"] = 2
    assert validez_router(s) == "valido"  # no encarcela el flujo


# ---------------------------------------------------------------------------
# Flujos end-to-end por instrumento
# ---------------------------------------------------------------------------

def test_e2e_inst_comp_dig():
    g = compile_graph()
    out = g.invoke(_base("INST-COMP-DIG-01"),
                   config={"configurable": {"thread_id": "t-cd"}})
    assert out["done"] is True
    assert out["psicometria"]["n_items_activos"] >= 6
    assert out["psicometria"]["alpha_cronbach"] > 0
    assert len(out["puntajes_individuales"]) == 40


def test_e2e_inst_raz_log_aplica_iteracion():
    """RL tiene RL-07 y RL-09 con sesgo alto → debe gatillar al menos 1 iteración."""
    g = compile_graph()
    out = g.invoke(_base("INST-RAZ-LOG-02"),
                   config={"configurable": {"thread_id": "t-rl"}})
    assert out["done"] is True
    assert out["iteracion_validez"] >= 1
    # Al menos algún ítem debe quedar excluido (por revisión o por psicometría)
    excluidos = len(out["items_rechazados_revision"]) + len(out["items_problematicos"])
    assert excluidos >= 1


def test_e2e_inst_esc_bie_likert():
    g = compile_graph()
    out = g.invoke(_base("INST-ESC-BIE-03"),
                   config={"configurable": {"thread_id": "t-bl"}})
    assert out["done"] is True
    assert out["instrument"]["formato"] == "likert"
    assert len(out["puntajes_individuales"]) == 50
    # En Likert, el puntaje bruto está entre n_items y 5*n_items
    n_items = out["psicometria"]["n_items_activos"]
    for ind in out["puntajes_individuales"]:
        assert n_items <= ind["puntaje_bruto"] <= 5 * n_items


def test_e2e_baremos_se_calculan():
    g = compile_graph()
    out = g.invoke(_base("INST-COMP-DIG-01"),
                   config={"configurable": {"thread_id": "t-bar"}})
    bar = out["baremos"]
    assert bar["n"] == 40
    assert bar["p25"] <= bar["p50"] <= bar["p75"]


def test_e2e_eventos_pipeline_completos():
    g = compile_graph()
    out = g.invoke(_base("INST-COMP-DIG-01"),
                   config={"configurable": {"thread_id": "t-evs"}})
    types = [e["type"] for e in out["events"]]
    for expected in [
        "especificacion_cargada",
        "items_revisados",
        "instrumento_ensamblado",
        "pilotaje_aplicado",
        "psicometria_calculada",
        "baremos_calibrados",
        "informes_individuales_generados",
        "informe_grupal_generado",
    ]:
        assert expected in types, f"falta evento {expected}"


def test_e2e_reporte_no_vacio():
    g = compile_graph()
    out = g.invoke(_base("INST-COMP-DIG-01"),
                   config={"configurable": {"thread_id": "t-rep"}})
    assert out["reporte"]
    assert "Informe psicométrico" in out["reporte"] or "α" in out["reporte"]


def test_e2e_percentiles_individuales_consistentes():
    g = compile_graph()
    out = g.invoke(_base("INST-COMP-DIG-01"),
                   config={"configurable": {"thread_id": "t-perc"}})
    for ind in out["puntajes_individuales"]:
        assert 0 <= ind["percentil"] <= 100
        assert ind["banda"] in {"bajo", "medio_bajo", "medio_alto", "alto"}
