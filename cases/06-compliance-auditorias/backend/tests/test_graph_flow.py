"""Tests del grafo LangGraph — Caso 06: Compliance & Auditorías."""
from src.graph import (
    ComplianceState,
    _append_traza,
    _hash_entry,
    _periodo_bounds,
    compile_graph,
    parsear_alcance,
    verificar_completitud,
)


def _base(audit_id: str = "AUD-001") -> ComplianceState:
    return {
        "audit_id": audit_id,
        "marco": "", "marco_nombre": "", "periodo": "", "descripcion_escenario": "",
        "controles_en_scope": [], "mapeo_controles": [],
        "evidencias": [], "cobertura": {}, "faltantes": [], "severidad_faltantes": "",
        "validaciones": [], "invalidas": [], "escalaciones": [],
        "expediente": {}, "trazabilidad": [],
        "score_cumplimiento": 0, "metricas": {}, "riesgo": "",
        "resumen": "", "events": [], "done": False,
    }


def test_graph_compiles():
    assert compile_graph() is not None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def test_periodo_bounds_quarter():
    s, e = _periodo_bounds("2026-Q1")
    assert s.year == 2026 and s.month == 1
    assert e.year == 2026 and e.month == 4


def test_periodo_bounds_month():
    s, e = _periodo_bounds("2026-03")
    assert s.year == 2026 and s.month == 3
    assert e.year == 2026 and e.month == 4


def test_hash_chain_changes_with_payload():
    h1 = _hash_entry("GENESIS", {"a": 1})
    h2 = _hash_entry("GENESIS", {"a": 2})
    assert h1 != h2
    assert len(h1) == 64


def test_traza_es_append_only_y_encadenada():
    t = []
    t = _append_traza(t, "accion1", {"k": 1})
    t = _append_traza(t, "accion2", {"k": 2})
    assert len(t) == 2
    assert t[0]["seq"] == 1 and t[1]["seq"] == 2
    assert t[1]["prev_hash"] == t[0]["hash"]
    assert t[0]["prev_hash"] == "GENESIS"


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def test_parsear_alcance_carga_escenario():
    out = parsear_alcance(_base("AUD-001"))
    assert out["marco"] == "ISO27001"
    assert out["periodo"] == "2026-Q1"
    assert len(out["controles_en_scope"]) == 4
    assert len(out["trazabilidad"]) == 1
    assert out["trazabilidad"][0]["accion"] == "parsear_alcance"


def test_router_severidad_alta_va_a_escalar():
    state = _base()
    state["severidad_faltantes"] = "alta"
    assert verificar_completitud(state) == "escalar_responsable"


def test_router_severidad_baja_va_a_validar():
    state = _base()
    state["severidad_faltantes"] = "baja"
    assert verificar_completitud(state) == "validar_evidencias"


# ---------------------------------------------------------------------------
# Flujos end-to-end por escenario
# ---------------------------------------------------------------------------

def test_e2e_aud001_iso_limpio():
    """AUD-001 → ISO 27001 con todas las evidencias presentes y vigentes."""
    g = compile_graph()
    out = g.invoke(_base("AUD-001"), config={"configurable": {"thread_id": "t-aud001"}})
    assert out["done"] is True
    assert out["riesgo"] == "verde"
    assert out["score_cumplimiento"] == 100
    assert out["faltantes"] == []
    assert out["escalaciones"] == []
    assert out["metricas"]["controles_completos"] == 4


def test_e2e_aud002_soc2_faltantes():
    """AUD-002 → SOC 2 con 2 controles incompletos en criticidad alta."""
    g = compile_graph()
    out = g.invoke(_base("AUD-002"), config={"configurable": {"thread_id": "t-aud002"}})
    assert out["done"] is True
    assert out["riesgo"] in ("amarillo", "rojo")
    assert out["score_cumplimiento"] < 100
    assert len(out["faltantes"]) >= 1
    assert len(out["escalaciones"]) >= 1
    assert out["severidad_faltantes"] == "alta"


def test_e2e_aud003_gdpr_evidencias_vencidas():
    """AUD-003 → GDPR con ROPA y DPIA vencidas → evidencias inválidas."""
    g = compile_graph()
    out = g.invoke(_base("AUD-003"), config={"configurable": {"thread_id": "t-aud003"}})
    assert out["done"] is True
    assert out["riesgo"] in ("amarillo", "rojo")
    assert len(out["invalidas"]) >= 1
    refs_invalidas = {v["ref"] for v in out["invalidas"]}
    assert "DPIA-2024-08" in refs_invalidas


def test_trazabilidad_se_extiende_en_cada_nodo():
    g = compile_graph()
    out = g.invoke(_base("AUD-002"), config={"configurable": {"thread_id": "t-traza"}})
    acciones = [t["accion"] for t in out["trazabilidad"]]
    for esperada in [
        "parsear_alcance", "mapear_controles", "recopilar_evidencias",
        "escalar_responsable", "validar_evidencias",
        "generar_expediente", "sellar_expediente",
    ]:
        assert esperada in acciones, f"falta accion {esperada}"
    # Encadenamiento
    for i in range(1, len(out["trazabilidad"])):
        assert out["trazabilidad"][i]["prev_hash"] == out["trazabilidad"][i - 1]["hash"]


def test_eventos_ciclo_completo_aud002():
    g = compile_graph()
    out = g.invoke(_base("AUD-002"), config={"configurable": {"thread_id": "t-events"}})
    types = [e["type"] for e in out["events"]]
    for expected in [
        "alcance_parseado", "controles_mapeados", "evidencias_recopiladas",
        "responsables_escalados", "evidencias_validadas",
        "expediente_generado", "trazabilidad_sellada", "auditoria_completada",
    ]:
        assert expected in types, f"falta evento {expected}"


def test_metricas_consistentes_aud001():
    g = compile_graph()
    out = g.invoke(_base("AUD-001"), config={"configurable": {"thread_id": "t-met"}})
    m = out["metricas"]
    assert m["score_cumplimiento"] == out["score_cumplimiento"]
    assert m["total_controles"] == len(out["mapeo_controles"])
    assert m["controles_completos"] + m["controles_parciales"] + m["controles_sin_evidencia"] == m["total_controles"]
    assert 0 <= m["score_cumplimiento"] <= 100


def test_expediente_contiene_indice_completo():
    g = compile_graph()
    out = g.invoke(_base("AUD-001"), config={"configurable": {"thread_id": "t-exp"}})
    exp = out["expediente"]
    assert exp["audit_id"] == "AUD-001"
    assert exp["marco"] == "ISO27001"
    assert len(exp["indice_por_control"]) == 4
    for ic in exp["indice_por_control"]:
        assert ic["estado"] in ("completo", "parcial", "sin_evidencia")
