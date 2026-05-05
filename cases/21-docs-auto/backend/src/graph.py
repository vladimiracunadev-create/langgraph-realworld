"""
graph.py — Grafo LangGraph para el Caso 21: Documentación Automática.

Pipeline con loop de revisión condicional (tope de iteraciones):

  escanear_repositorio → extraer_artefactos → generar_outline → redactar_secciones
       → qa_precision_tecnica
            ├─ imprecisiones>0 (y iter<max) → revisar_secciones → qa_precision_tecnica
            └─ ok → qa_coherencia_global → publicar_documentacion → producir_resumen → END

DEMO: redacción determinista a partir de los artefactos extraídos del repo
(sin LLM, sin red). LIVE opt-in con OPENAI_API_KEY para resumen ejecutivo.
"""
from __future__ import annotations

import logging
import operator
import os
from datetime import datetime
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import get_outline_template, get_quality_rules, get_repo
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class DocsState(TypedDict):
    repo_id: str
    repo: dict
    artefactos: dict
    outline: list
    secciones: list
    issues: list
    iter_revision: int
    score_global: int
    coherencia: dict
    documento_md: str
    diff: dict
    metricas: dict
    riesgo: str
    resumen: str
    events: Annotated[list, operator.add]
    done: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _llm_invoke(prompt: str, fallback: str) -> str:
    if not _LIVE_MODE:
        return fallback
    try:
        from langchain_openai import ChatOpenAI  # noqa: PLC0415
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model_name, temperature=0)
        return llm.invoke(prompt).content
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM no disponible, fallback DEMO: %s", exc)
        return fallback


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def escanear_repositorio(state: DocsState) -> dict:
    repo_id = state.get("repo_id", "DOC-001")
    repo = get_repo(repo_id, get_data_dir())

    total_loc = sum(m.get("loc", 0) for m in repo.get("modulos", []))
    total_modulos = len(repo.get("modulos", []))

    logger.info(
        "Repositorio escaneado: id=%s nombre=%s modulos=%d loc=%d",
        repo_id, repo.get("nombre"), total_modulos, total_loc,
    )

    return {
        "repo": repo,
        "events": [{
            "type": "repositorio_escaneado",
            "repo_id": repo_id,
            "nombre": repo.get("nombre"),
            "tipo": repo.get("tipo"),
            "total_modulos": total_modulos,
            "total_loc": total_loc,
        }],
    }


def extraer_artefactos(state: DocsState) -> dict:
    repo = state.get("repo", {})
    endpoints: list = []
    funciones: list = []
    schemas: list = []
    docstring_ratios: list = []

    for m in repo.get("modulos", []):
        for ep in m.get("endpoints", []):
            endpoints.append({
                "method": ep.get("method"),
                "path": ep.get("path"),
                "handler": ep.get("handler"),
                "doc": ep.get("doc", ""),
                "modulo": m.get("path"),
            })
        for fn in m.get("funciones_publicas", []):
            funciones.append({"nombre": fn, "modulo": m.get("path")})
        for sc in m.get("schemas", []):
            schemas.append({"nombre": sc, "modulo": m.get("path")})
        if m.get("docstring_ratio") is not None:
            docstring_ratios.append(m.get("docstring_ratio", 0.0))

    docstring_ratio_promedio = (
        sum(docstring_ratios) / len(docstring_ratios) if docstring_ratios else 0.0
    )

    artefactos = {
        "endpoints": endpoints,
        "funciones_publicas": funciones,
        "schemas": schemas,
        "tests": repo.get("tests", {}),
        "changelog_entries": repo.get("changelog_entries", 0),
        "readme_existente": repo.get("readme_existente", False),
        "ci_configurado": repo.get("ci_configurado", False),
        "docstring_ratio_promedio": round(docstring_ratio_promedio, 2),
    }

    logger.info(
        "Artefactos extraídos: endpoints=%d funciones=%d schemas=%d docstring_ratio=%.2f",
        len(endpoints), len(funciones), len(schemas), docstring_ratio_promedio,
    )

    return {
        "artefactos": artefactos,
        "events": [{
            "type": "artefactos_extraidos",
            "endpoints": len(endpoints),
            "funciones_publicas": len(funciones),
            "schemas": len(schemas),
            "docstring_ratio_promedio": round(docstring_ratio_promedio, 2),
        }],
    }


def generar_outline(state: DocsState) -> dict:
    repo = state.get("repo", {})
    tipo = repo.get("tipo", "api_rest")
    outline = get_outline_template(tipo, get_data_dir())

    if not outline:
        outline = [
            {"id": "overview", "titulo": "Visión general", "descripcion": "Resumen del proyecto."},
            {"id": "instalacion", "titulo": "Instalación", "descripcion": "Cómo instalarlo."},
            {"id": "uso", "titulo": "Uso", "descripcion": "Ejemplos básicos."},
        ]

    logger.info("Outline generado: tipo=%s secciones=%d", tipo, len(outline))

    return {
        "outline": outline,
        "events": [{
            "type": "outline_generado",
            "tipo_proyecto": tipo,
            "total_secciones": len(outline),
            "ids": [s["id"] for s in outline],
        }],
    }


def _render_seccion(sec_id: str, repo: dict, art: dict) -> str:
    """Genera contenido determinista para una sección a partir de artefactos."""
    if sec_id == "overview":
        return (
            f"# {repo.get('nombre','(sin nombre)')}\n\n"
            f"{repo.get('descripcion','')}\n\n"
            f"- **Lenguaje**: {repo.get('lenguaje','—')}\n"
            f"- **Framework**: {repo.get('framework','—')}\n"
            f"- **Versión**: {repo.get('version','—')}\n"
        )
    if sec_id == "instalacion":
        return (
            "## Instalación\n\n"
            "```bash\n"
            f"git clone <repo-url> {repo.get('nombre','proyecto')}\n"
            f"cd {repo.get('nombre','proyecto')}\n"
            "pip install -r requirements.txt\n"
            "```\n"
        )
    if sec_id == "uso":
        ep = (art.get("endpoints") or [{}])[0]
        return (
            "## Uso rápido\n\n"
            "```bash\n"
            f"uvicorn src.api:app --reload\n"
            f"curl -X {ep.get('method','GET')} http://localhost:8000{ep.get('path','/')}\n"
            "```\n"
        ) if ep.get("path") else "## Uso rápido\n\nLevantar el servicio y consumir sus endpoints.\n"
    if sec_id == "endpoints":
        if not art.get("endpoints"):
            return "## Endpoints\n\nNo se detectaron endpoints en el código.\n"
        rows = "| Método | Ruta | Handler | Descripción |\n|---|---|---|---|\n"
        for ep in art["endpoints"]:
            doc = ep.get("doc") or "_(sin descripción)_"
            rows += f"| `{ep.get('method')}` | `{ep.get('path')}` | `{ep.get('handler')}` | {doc} |\n"
        return "## Endpoints\n\n" + rows
    if sec_id == "modelo":
        if not art.get("schemas"):
            return "## Modelo de datos\n\nNo se detectaron schemas declarados.\n"
        items = "\n".join(f"- `{s['nombre']}` (en `{s['modulo']}`)" for s in art["schemas"])
        return "## Modelo de datos\n\n" + items + "\n"
    if sec_id == "integraciones":
        if not art.get("funciones_publicas"):
            return "## Integraciones externas\n\nNo se detectaron funciones públicas.\n"
        items = "\n".join(f"- `{f['nombre']}()` en `{f['modulo']}`" for f in art["funciones_publicas"])
        return "## Integraciones externas\n\n" + items + "\n"
    if sec_id == "tests":
        t = art.get("tests", {})
        return (
            "## Tests y cobertura\n\n"
            f"- Total: **{t.get('total', 0)}**\n"
            f"- Pasando: **{t.get('passing', 0)}**\n"
            f"- Cobertura: **{t.get('cobertura_pct', 0)}%**\n"
        )
    if sec_id == "changelog":
        n = art.get("changelog_entries", 0)
        return (
            "## Changelog\n\n"
            f"Hay **{n}** entradas en el changelog.\n"
            if n > 0 else "## Changelog\n\nNo hay changelog disponible.\n"
        )
    if sec_id == "operacion":
        return (
            "## Operación\n\n"
            "- Monitorear `/health` cada 30 s.\n"
            "- Ante fallos, revisar logs estructurados (JSON).\n"
            "- Reintentos automáticos con backoff exponencial.\n"
        )
    return f"## {sec_id}\n\nContenido pendiente.\n"


def redactar_secciones(state: DocsState) -> dict:
    repo = state.get("repo", {})
    art = state.get("artefactos", {})
    outline = state.get("outline", [])

    secciones: list = []
    for sec in outline:
        sec_id = sec["id"]
        contenido = _render_seccion(sec_id, repo, art)
        secciones.append({
            "id": sec_id,
            "titulo": sec.get("titulo", sec_id),
            "contenido": contenido,
            "estado": "borrador",
            "score": 0,
            "issues": [],
        })

    logger.info("Secciones redactadas: %d", len(secciones))

    return {
        "secciones": secciones,
        "iter_revision": 0,
        "events": [{
            "type": "secciones_redactadas",
            "total": len(secciones),
            "ids": [s["id"] for s in secciones],
        }],
    }


def qa_precision_tecnica(state: DocsState) -> dict:
    """
    Verifica que cada sección referencie artefactos reales del repo.
    Calcula score por sección y lista de issues.
    """
    rules = get_quality_rules(get_data_dir())
    umbral = rules.get("umbral_score_seccion", 80)
    pen = rules.get("penalizaciones", {})
    cobertura_baja_pct = rules.get("umbral_cobertura_baja_pct", 60)

    art = state.get("artefactos", {})
    secciones = list(state.get("secciones", []))
    all_issues: list = []

    endpoints = art.get("endpoints", [])
    endpoints_sin_doc = [ep for ep in endpoints if not (ep.get("doc") or "").strip()]
    funciones = art.get("funciones_publicas", [])
    docstring_ratio = art.get("docstring_ratio_promedio", 1.0)
    funciones_sin_docstring_estimadas = int(round(len(funciones) * (1 - docstring_ratio)))

    for sec in secciones:
        score = 100
        issues_sec: list = []
        contenido = sec.get("contenido", "")

        if sec["id"] == "endpoints" and endpoints_sin_doc:
            penal = pen.get("endpoint_sin_doc", 8) * len(endpoints_sin_doc)
            score -= penal
            for ep in endpoints_sin_doc:
                issues_sec.append({
                    "tipo": "endpoint_sin_doc",
                    "ref": f"{ep['method']} {ep['path']}",
                    "mensaje": "Endpoint sin descripción en el código fuente.",
                })

        if sec["id"] in ("integraciones", "modelo") and funciones_sin_docstring_estimadas > 0:
            penal = pen.get("funcion_sin_docstring", 4) * funciones_sin_docstring_estimadas
            score -= penal
            issues_sec.append({
                "tipo": "funciones_sin_docstring",
                "ref": f"~{funciones_sin_docstring_estimadas} funciones",
                "mensaje": "Hay funciones públicas sin docstring que reducen la precisión técnica.",
            })

        if sec["id"] == "tests":
            t = art.get("tests", {}) or {}
            if t.get("passing", 0) < t.get("total", 0):
                fallos = t["total"] - t["passing"]
                score -= pen.get("tests_fallando", 12)
                issues_sec.append({
                    "tipo": "tests_fallando",
                    "ref": f"{fallos} test(s) fallando",
                    "mensaje": "Tests fallando — la documentación de cobertura puede ser engañosa.",
                })
            if t.get("cobertura_pct", 100) < cobertura_baja_pct:
                score -= pen.get("cobertura_baja", 8)
                issues_sec.append({
                    "tipo": "cobertura_baja",
                    "ref": f"{t.get('cobertura_pct',0)}%",
                    "mensaje": f"Cobertura debajo del umbral mínimo de {cobertura_baja_pct}%.",
                })

        if sec["id"] == "changelog" and art.get("changelog_entries", 0) == 0:
            score -= pen.get("sin_changelog", 10)
            issues_sec.append({
                "tipo": "sin_changelog",
                "ref": "CHANGELOG",
                "mensaje": "No hay entradas en el changelog para documentar.",
            })

        if sec["id"] == "instalacion" and not art.get("readme_existente", False):
            score -= pen.get("sin_readme", 15)
            issues_sec.append({
                "tipo": "sin_readme",
                "ref": "README",
                "mensaje": "No existe README de referencia en el repo.",
            })

        if sec["id"] == "operacion" and not art.get("ci_configurado", False):
            score -= pen.get("sin_ci", 6)
            issues_sec.append({
                "tipo": "sin_ci",
                "ref": "CI",
                "mensaje": "No hay CI configurado — operación menos confiable.",
            })

        score = max(score, 0)
        sec["score"] = score
        sec["issues"] = issues_sec
        sec["estado"] = "aprobada" if score >= umbral else "requiere_revision"
        all_issues.extend([{**i, "seccion": sec["id"]} for i in issues_sec])

    pendientes = sum(1 for s in secciones if s["estado"] == "requiere_revision")
    iter_actual = state.get("iter_revision", 0)

    logger.info(
        "QA precisión técnica iter=%d: %d secciones, %d con issues, %d pendientes",
        iter_actual, len(secciones), sum(1 for s in secciones if s["issues"]), pendientes,
    )

    return {
        "secciones": secciones,
        "issues": all_issues,
        "events": [{
            "type": "qa_precision_completado",
            "iter": iter_actual,
            "total_secciones": len(secciones),
            "aprobadas": len(secciones) - pendientes,
            "requieren_revision": pendientes,
            "total_issues": len(all_issues),
        }],
    }


def revisar_secciones(state: DocsState) -> dict:
    """Aplica correcciones a las secciones que aún no aprueban."""
    secciones = list(state.get("secciones", []))
    revisadas = 0
    for sec in secciones:
        if sec.get("estado") == "requiere_revision":
            nota = (
                "\n\n> _Nota del agente: esta sección fue revisada automáticamente. "
                "Las imprecisiones detectadas se reportan al equipo (ver issues)._\n"
            )
            if nota not in sec.get("contenido", ""):
                sec["contenido"] = sec["contenido"] + nota
            sec["estado"] = "revisada"
            revisadas += 1

    iter_revision = state.get("iter_revision", 0) + 1
    logger.info("Revisión aplicada: iter=%d secciones_revisadas=%d", iter_revision, revisadas)

    return {
        "secciones": secciones,
        "iter_revision": iter_revision,
        "events": [{
            "type": "secciones_revisadas",
            "iter": iter_revision,
            "revisadas": revisadas,
        }],
    }


def calidad_seccion_router(state: DocsState) -> Literal["revisar_secciones", "qa_coherencia_global"]:
    """Router: si hay secciones pendientes Y aún quedan iteraciones → revisar; si no → seguir."""
    rules = get_quality_rules(get_data_dir())
    max_iter = rules.get("max_iteraciones_revision", 3)
    pendientes = sum(1 for s in state.get("secciones", []) if s.get("estado") == "requiere_revision")
    if pendientes > 0 and state.get("iter_revision", 0) < max_iter:
        return "revisar_secciones"
    return "qa_coherencia_global"


def qa_coherencia_global(state: DocsState) -> dict:
    """Calcula score global y métrica de coherencia terminológica."""
    rules = get_quality_rules(get_data_dir())
    umbrales = rules.get("umbral_riesgo", {"verde_min_score": 90, "amarillo_min_score": 70})
    secciones = state.get("secciones", [])
    scores = [s.get("score", 0) for s in secciones]
    score_global = round(sum(scores) / len(scores)) if scores else 0

    nombre_repo = state.get("repo", {}).get("nombre", "")
    menciones_repo = sum(1 for s in secciones if nombre_repo and nombre_repo in s.get("contenido", ""))
    coherencia = {
        "menciones_repo": menciones_repo,
        "secciones_aprobadas": sum(1 for s in secciones if s.get("estado") in ("aprobada", "revisada")),
        "secciones_requieren_revision": sum(1 for s in secciones if s.get("estado") == "requiere_revision"),
    }

    if score_global >= umbrales["verde_min_score"] and coherencia["secciones_requieren_revision"] == 0:
        riesgo = "verde"
    elif score_global >= umbrales["amarillo_min_score"]:
        riesgo = "amarillo"
    else:
        riesgo = "rojo"

    logger.info(
        "QA coherencia global: score=%d riesgo=%s coherencia=%s",
        score_global, riesgo, coherencia,
    )

    return {
        "score_global": score_global,
        "coherencia": coherencia,
        "riesgo": riesgo,
        "events": [{
            "type": "qa_global_completado",
            "score_global": score_global,
            "riesgo": riesgo,
            "secciones_aprobadas": coherencia["secciones_aprobadas"],
            "secciones_pendientes": coherencia["secciones_requieren_revision"],
        }],
    }


def publicar_documentacion(state: DocsState) -> dict:
    """Compone el documento final en Markdown y calcula diff vs versión previa (placeholder)."""
    secciones = state.get("secciones", [])
    cuerpo = "\n\n---\n\n".join(s.get("contenido", "") for s in secciones)
    documento_md = (
        f"<!-- Generado por agente de documentación · {_now_iso()} -->\n\n" + cuerpo
    )

    diff = {
        "secciones_agregadas": len(secciones),
        "secciones_modificadas": sum(1 for s in secciones if s.get("estado") == "revisada"),
        "secciones_intactas": sum(1 for s in secciones if s.get("estado") == "aprobada"),
        "lineas_totales": documento_md.count("\n"),
    }

    metricas = {
        "score_global": state.get("score_global", 0),
        "total_secciones": len(secciones),
        "iteraciones_revision": state.get("iter_revision", 0),
        "issues_detectadas": len(state.get("issues", [])),
        "lineas_documento": diff["lineas_totales"],
    }

    logger.info(
        "Documento publicado: lineas=%d secciones=%d iter=%d",
        diff["lineas_totales"], len(secciones), state.get("iter_revision", 0),
    )

    return {
        "documento_md": documento_md,
        "diff": diff,
        "metricas": metricas,
        "events": [{
            "type": "documentacion_publicada",
            "lineas": diff["lineas_totales"],
            "secciones": len(secciones),
            "diff": diff,
        }],
    }


def producir_resumen(state: DocsState) -> dict:
    metricas = state.get("metricas", {})
    repo = state.get("repo", {})
    score = state.get("score_global", 0)
    riesgo = state.get("riesgo", "")
    riesgo_label = {"verde": "BAJO", "amarillo": "MEDIO", "rojo": "ALTO"}.get(riesgo, riesgo.upper())

    fallback = (
        f"## Resumen — Documentación de **{repo.get('nombre','(sin nombre)')}**\n\n"
        f"**Score:** {score}/100 · **Riesgo:** {riesgo_label}\n\n"
        f"### Estadísticas\n"
        f"- Secciones generadas: {metricas.get('total_secciones', 0)}\n"
        f"- Iteraciones de revisión: {metricas.get('iteraciones_revision', 0)}\n"
        f"- Issues detectadas: {metricas.get('issues_detectadas', 0)}\n"
        f"- Líneas del documento final: {metricas.get('lineas_documento', 0)}\n\n"
        f"### Próximos pasos\n"
        f"- Resolver las issues marcadas para subir el score a {state.get('score_global',0)+10}+.\n"
        f"- Publicar el documento en MkDocs/Confluence/Notion.\n\n"
        f"_Generado por agente de docs · Caso 21. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres tech writer senior. Redacta un resumen ejecutivo en español (máx 180 palabras) "
            f"sobre la documentación generada para el repo {repo.get('nombre')} "
            f"(score {score}/100, riesgo {riesgo_label}, "
            f"{metricas.get('total_secciones',0)} secciones, "
            f"{metricas.get('iteraciones_revision',0)} iteraciones de revisión, "
            f"{metricas.get('issues_detectadas',0)} issues detectadas). "
            f"Cierra con próximos pasos concretos para el equipo de ingeniería."
        )
        resumen = _llm_invoke(prompt, fallback)
    else:
        resumen = fallback

    logger.info(
        "Resumen generado: repo=%s score=%s riesgo=%s modo=%s",
        repo.get("nombre"), score, riesgo, "LIVE" if _LIVE_MODE else "DEMO",
    )

    return {
        "resumen": resumen,
        "done": True,
        "events": [{
            "type": "documentacion_completada",
            "repo": repo.get("nombre"),
            "score": score,
            "riesgo": riesgo,
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(DocsState)

    builder.add_node("escanear_repositorio", escanear_repositorio)
    builder.add_node("extraer_artefactos", extraer_artefactos)
    builder.add_node("generar_outline", generar_outline)
    builder.add_node("redactar_secciones", redactar_secciones)
    builder.add_node("qa_precision_tecnica", qa_precision_tecnica)
    builder.add_node("revisar_secciones", revisar_secciones)
    builder.add_node("qa_coherencia_global", qa_coherencia_global)
    builder.add_node("publicar_documentacion", publicar_documentacion)
    builder.add_node("producir_resumen", producir_resumen)

    builder.set_entry_point("escanear_repositorio")
    builder.add_edge("escanear_repositorio", "extraer_artefactos")
    builder.add_edge("extraer_artefactos", "generar_outline")
    builder.add_edge("generar_outline", "redactar_secciones")
    builder.add_edge("redactar_secciones", "qa_precision_tecnica")

    builder.add_conditional_edges(
        "qa_precision_tecnica",
        calidad_seccion_router,
        {
            "revisar_secciones": "revisar_secciones",
            "qa_coherencia_global": "qa_coherencia_global",
        },
    )
    builder.add_edge("revisar_secciones", "qa_precision_tecnica")
    builder.add_edge("qa_coherencia_global", "publicar_documentacion")
    builder.add_edge("publicar_documentacion", "producir_resumen")
    builder.add_edge("producir_resumen", END)

    return builder.compile(checkpointer=MemorySaver())
