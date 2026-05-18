"""Tests del grafo LangGraph — Caso 18: Marketing con QA."""
from src.graph import (
    MarketingState,
    _render_borrador,
    compile_graph,
    estilo_router,
    generar_borrador,
    hechos_router,
    parsear_brief,
)


def _base(brief_id: str = "BR-001") -> MarketingState:
    return {
        "brief_id": brief_id, "brief": {}, "borrador": "",
        "estilo": {}, "hechos": {}, "seo": {},
        "iter_estilo": 0, "iter_hechos": 0,
        "alucinaciones_retiradas_total": 0,
        "hechos_inyectados_total": 0,
        "score_global": 0, "riesgo": "", "decision_editor": "",
        "contenido_final": "", "diff": {}, "metricas": {},
        "resumen": "", "events": [], "done": False,
    }


def test_graph_compiles():
    assert compile_graph() is not None


# Helpers / render

def test_render_borrador_blog_incluye_titulo_y_keywords():
    brief = {
        "formato": "blog_post",
        "titulo": "Mi Post",
        "audiencia": "devs",
        "keywords": ["python", "api"],
        "hechos_obligatorios": [{"id": "F1", "claim": "X", "source_id": "S"}],
    }
    out = _render_borrador(brief)
    assert "Mi Post" in out
    assert "python" in out and "api" in out
    assert "X" in out


def test_render_borrador_email_tiene_cta():
    brief = {"formato": "email", "titulo": "Hola", "audiencia": "x", "keywords": [], "hechos_obligatorios": []}
    out = _render_borrador(brief)
    assert "demo" in out.lower()


# Nodos

def test_parsear_brief_carga_br001():
    out = parsear_brief(_base("BR-001"))
    assert out["brief"]["titulo"].startswith("Lanzamiento")
    assert out["iter_estilo"] == 0
    assert out["iter_hechos"] == 0


def test_generar_borrador_incluye_hechos_clave():
    state = _base("BR-001")
    state["brief"] = parsear_brief(state)["brief"]
    out = generar_borrador(state)
    assert "49 USD/mes" in out["borrador"]


# Routers

def test_estilo_router_loop_si_no_ok_y_hay_iter():
    state = _base()
    state["estilo"] = {"ok": False}
    state["iter_estilo"] = 0
    assert estilo_router(state) == "reescribir_tono"


def test_estilo_router_avanza_si_ok():
    state = _base()
    state["estilo"] = {"ok": True}
    assert estilo_router(state) == "verificar_hechos"


def test_estilo_router_avanza_si_agotado():
    state = _base()
    state["estilo"] = {"ok": False}
    state["iter_estilo"] = 5
    assert estilo_router(state) == "verificar_hechos"


def test_hechos_router_loop_si_no_ok():
    state = _base()
    state["hechos"] = {"ok": False}
    state["iter_hechos"] = 0
    assert hechos_router(state) == "corregir_hechos"


def test_hechos_router_avanza_si_ok():
    state = _base()
    state["hechos"] = {"ok": True}
    assert hechos_router(state) == "optimizar_seo"


# Flujos end-to-end

def test_e2e_br001_brief_limpio():
    g = compile_graph()
    out = g.invoke(_base("BR-001"), config={"configurable": {"thread_id": "t-br001"}})
    assert out["done"] is True
    assert out["riesgo"] in ("verde", "amarillo")
    assert out["score_global"] >= 70
    assert "Lanzamiento" in out["contenido_final"]
    # BR-001 no tiene claims riesgosos
    assert out["iter_hechos"] == 0


def test_e2e_br002_email_con_alucinaciones():
    g = compile_graph()
    out = g.invoke(_base("BR-002"), config={"configurable": {"thread_id": "t-br002"}})
    assert out["done"] is True
    # Debe haber iterado en hechos al menos una vez por las claims riesgosas
    assert out["iter_hechos"] >= 1
    assert out["diff"]["alucinaciones_retiradas"] >= 1


def test_e2e_br003_landing_legacy():
    g = compile_graph()
    out = g.invoke(_base("BR-003"), config={"configurable": {"thread_id": "t-br003"}})
    assert out["done"] is True
    # BR-003: 3 claims riesgosos + tono formal/legacy
    assert out["iter_hechos"] >= 1
    assert out["riesgo"] in ("verde", "amarillo", "rojo")


def test_eventos_completos_br001():
    g = compile_graph()
    out = g.invoke(_base("BR-001"), config={"configurable": {"thread_id": "t-events"}})
    types = [e["type"] for e in out["events"]]
    for esperado in [
        "brief_parseado", "borrador_generado", "estilo_revisado",
        "hechos_verificados", "seo_optimizado", "editor_decidio",
        "contenido_publicado", "marketing_completado",
    ]:
        assert esperado in types, f"falta evento {esperado}"


def test_metricas_consistentes_br002():
    g = compile_graph()
    out = g.invoke(_base("BR-002"), config={"configurable": {"thread_id": "t-met"}})
    m = out["metricas"]
    assert m["score_global"] == out["score_global"]
    assert m["iter_estilo"] == out["iter_estilo"]
    assert m["iter_hechos"] == out["iter_hechos"]
    assert 0 <= m["score_global"] <= 100


def test_contenido_final_no_contiene_alucinaciones_br002():
    g = compile_graph()
    out = g.invoke(_base("BR-002"), config={"configurable": {"thread_id": "t-clean"}})
    # Después del loop, las claims riesgosas deben estar retiradas
    contenido = out["contenido_final"]
    assert "ROI del 300%" not in contenido
    assert "#1 del mundo" not in contenido or "[afirmación retirada" in contenido


def test_decision_editor_alineada_con_riesgo():
    g = compile_graph()
    out = g.invoke(_base("BR-001"), config={"configurable": {"thread_id": "t-decision"}})
    riesgo = out["riesgo"]
    decision = out["decision_editor"]
    if riesgo == "verde":
        assert decision == "aprobado"
    elif riesgo == "amarillo":
        assert decision == "aprobado_con_observaciones"
    else:
        assert decision == "rechazado"
