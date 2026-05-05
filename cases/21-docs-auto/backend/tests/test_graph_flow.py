"""Tests del grafo LangGraph — Caso 21: Documentación Automática."""
from src.graph import (
    DocsState,
    _render_seccion,
    calidad_seccion_router,
    compile_graph,
    escanear_repositorio,
    extraer_artefactos,
)


def _base(repo_id: str = "DOC-001") -> DocsState:
    return {
        "repo_id": repo_id, "repo": {}, "artefactos": {},
        "outline": [], "secciones": [], "issues": [],
        "iter_revision": 0, "score_global": 0, "coherencia": {},
        "documento_md": "", "diff": {}, "metricas": {},
        "riesgo": "", "resumen": "", "events": [], "done": False,
    }


def test_graph_compiles():
    assert compile_graph() is not None


# Helpers

def test_render_overview_incluye_nombre():
    repo = {"nombre": "demo-svc", "descripcion": "x", "lenguaje": "python"}
    out = _render_seccion("overview", repo, {})
    assert "demo-svc" in out
    assert "python" in out


def test_render_endpoints_lista_todo():
    art = {"endpoints": [
        {"method": "GET", "path": "/a", "handler": "h1", "doc": "d1"},
        {"method": "POST", "path": "/b", "handler": "h2", "doc": ""},
    ]}
    out = _render_seccion("endpoints", {}, art)
    assert "/a" in out and "/b" in out
    assert "h1" in out and "h2" in out


# Nodos

def test_escanear_carga_repo():
    out = escanear_repositorio(_base("DOC-001"))
    assert out["repo"]["nombre"] == "fastapi-orders"


def test_extraer_artefactos_cuenta_endpoints():
    state = _base("DOC-001")
    state["repo"] = escanear_repositorio(state)["repo"]
    out = extraer_artefactos(state)
    art = out["artefactos"]
    assert len(art["endpoints"]) == 4
    assert art["docstring_ratio_promedio"] == 1.0


def test_router_loop_revisa_si_pendientes_y_iter_disponibles():
    state = _base()
    state["secciones"] = [
        {"id": "x", "estado": "requiere_revision", "score": 50, "issues": []},
    ]
    state["iter_revision"] = 0
    assert calidad_seccion_router(state) == "revisar_secciones"


def test_router_loop_avanza_si_sin_pendientes():
    state = _base()
    state["secciones"] = [{"id": "x", "estado": "aprobada", "score": 95, "issues": []}]
    state["iter_revision"] = 0
    assert calidad_seccion_router(state) == "qa_coherencia_global"


def test_router_loop_avanza_al_agotar_iteraciones():
    state = _base()
    state["secciones"] = [{"id": "x", "estado": "requiere_revision", "score": 30, "issues": []}]
    state["iter_revision"] = 3
    assert calidad_seccion_router(state) == "qa_coherencia_global"


# Flujos end-to-end

def test_e2e_doc001_proyecto_limpio():
    g = compile_graph()
    out = g.invoke(_base("DOC-001"), config={"configurable": {"thread_id": "t-doc001"}})
    assert out["done"] is True
    assert out["riesgo"] == "verde"
    assert out["score_global"] >= 90
    assert out["iter_revision"] == 0
    assert "fastapi-orders" in out["documento_md"]


def test_e2e_doc002_proyecto_parcial():
    g = compile_graph()
    out = g.invoke(_base("DOC-002"), config={"configurable": {"thread_id": "t-doc002"}})
    assert out["done"] is True
    # DOC-002 tiene endpoints sin doc + tests fallando: el agente debe detectar ambas issues.
    assert len(out["issues"]) >= 2
    assert any(i["tipo"] == "endpoint_sin_doc" for i in out["issues"])
    assert any(i["tipo"] == "tests_fallando" for i in out["issues"])


def test_e2e_doc003_legacy_aplica_revisiones():
    g = compile_graph()
    out = g.invoke(_base("DOC-003"), config={"configurable": {"thread_id": "t-doc003"}})
    assert out["done"] is True
    assert out["riesgo"] in ("amarillo", "rojo")
    assert out["iter_revision"] >= 1
    assert out["iter_revision"] <= 3
    assert any(i["tipo"] == "tests_fallando" for i in out["issues"])


def test_eventos_completos_doc001():
    g = compile_graph()
    out = g.invoke(_base("DOC-001"), config={"configurable": {"thread_id": "t-events"}})
    types = [e["type"] for e in out["events"]]
    for esperado in [
        "repositorio_escaneado", "artefactos_extraidos", "outline_generado",
        "secciones_redactadas", "qa_precision_completado",
        "qa_global_completado", "documentacion_publicada", "documentacion_completada",
    ]:
        assert esperado in types, f"falta evento {esperado}"


def test_metricas_consistentes_doc002():
    g = compile_graph()
    out = g.invoke(_base("DOC-002"), config={"configurable": {"thread_id": "t-met"}})
    m = out["metricas"]
    assert m["total_secciones"] == len(out["secciones"])
    assert m["score_global"] == out["score_global"]
    assert m["issues_detectadas"] == len(out["issues"])
    assert 0 <= m["score_global"] <= 100


def test_documento_contiene_todas_las_secciones():
    g = compile_graph()
    out = g.invoke(_base("DOC-001"), config={"configurable": {"thread_id": "t-doc-md"}})
    md_lower = out["documento_md"].lower()
    for sec in out["secciones"]:
        # Cada sección debe estar reflejada por su título o por keywords del contenido renderizado
        assert sec["contenido"].split("\n", 1)[0].strip().lower() in md_lower
