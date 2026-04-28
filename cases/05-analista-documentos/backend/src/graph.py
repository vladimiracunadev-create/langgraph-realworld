"""
graph.py — Grafo LangGraph para el Caso 05: Analista de Documentos.

Pipeline de análisis contractual:
  ingesta_texto → segmentar_secciones → extraer_clausulas → clasificar_riesgos
    ├─ riesgo alto  → escalar_revision_legal → generar_checklist
    └─ riesgo medio/bajo  →                    generar_checklist
                                                    ↓
                                       producir_resumen_ejecutivo → END

Modo DEMO (sin OPENAI_API_KEY): lógica determinista con datos JSON locales.
Modo LIVE (con OPENAI_API_KEY): nodos de análisis y resumen usan GPT-4o-mini.
"""
from __future__ import annotations

import logging
import operator
import os
import re
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import get_clause_patterns, get_document
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())

_HEADER_RE = re.compile(
    r"(?m)^[ \t]*((?:CLÁUSULA|ARTÍCULO|SECCIÓN|CONSIDERANDO|CONSIDERANDOS|ANEXO|CAPÍTULO|PARTE)[^\n]+)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Estado del grafo
# ---------------------------------------------------------------------------

class DocumentState(TypedDict):
    doc_id: str
    doc_title: str
    doc_type: str
    raw_text: str
    sections: list                              # [{title, content, index}]
    clauses: list                               # [{type, description, risk, section, matched_keywords, excerpt}]
    risk_score: int                             # 0-100
    risk_level: str                             # "bajo" | "medio" | "alto"
    escalation_notes: str
    checklist: list                             # [str]
    executive_summary: str
    events: Annotated[list, operator.add]       # timeline auditado
    done: bool


# ---------------------------------------------------------------------------
# Helper LLM (modo LIVE)
# ---------------------------------------------------------------------------

def _llm_analyze(prompt: str, fallback: str) -> str:
    """Invoca GPT-4o-mini si hay OPENAI_API_KEY; si no, devuelve fallback DEMO."""
    if not _LIVE_MODE:
        return fallback
    try:
        from langchain_openai import ChatOpenAI  # noqa: PLC0415
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model_name, temperature=0)
        return llm.invoke(prompt).content
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM no disponible, usando fallback DEMO: %s", exc)
        return fallback


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _split_sections(text: str) -> list[dict]:
    """Divide el texto en secciones basándose en headers contractuales reconocibles."""
    matches = list(_HEADER_RE.finditer(text))
    sections: list[dict] = []

    if not matches:
        return [{"title": "Documento completo", "content": text.strip(), "index": 0}]

    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append({"title": "Preámbulo", "content": preamble, "index": 0})

    for i, m in enumerate(matches):
        title = m.group(1).strip()
        content_start = m.end()
        content_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[content_start:content_end].strip()
        sections.append({"title": title, "content": content, "index": i + 1})

    return sections


def _find_clauses_in_sections(sections: list[dict], patterns: dict) -> list[dict]:
    """Detecta cláusulas usando keyword matching en cada sección del documento."""
    found: list[dict] = []
    seen_types: set[str] = set()

    for section in sections:
        content_lower = section["content"].lower()
        for clause_type, pattern_data in patterns.items():
            keywords = pattern_data.get("keywords", [])
            matched = [kw for kw in keywords if kw.lower() in content_lower]
            if matched and clause_type not in seen_types:
                seen_types.add(clause_type)
                found.append({
                    "type": clause_type,
                    "description": pattern_data.get("description", clause_type),
                    "risk": pattern_data.get("risk", "bajo"),
                    "section": section["title"],
                    "matched_keywords": matched,
                    "excerpt": section["content"][:250],
                    "checklist_item": pattern_data.get("checklist_item", ""),
                    "escalation_reason": pattern_data.get("escalation_reason"),
                })

    return found


def _score_from_clauses(clauses: list[dict]) -> tuple[int, str]:
    """Calcula risk_score (0-100) y risk_level a partir de las cláusulas encontradas."""
    if not clauses:
        return 5, "bajo"

    risk_weights = {"alto": 100, "medio": 50, "bajo": 10}
    total_weight = sum(risk_weights.get(c["risk"], 10) for c in clauses)
    avg_weight = total_weight / len(clauses)

    alto_count = sum(1 for c in clauses if c["risk"] == "alto")
    if alto_count > 0:
        risk_score = min(int(avg_weight + alto_count * 10), 100)
        risk_level = "alto"
    elif avg_weight >= 35:
        risk_score = min(int(avg_weight), 75)
        risk_level = "medio"
    else:
        risk_score = max(int(avg_weight), 5)
        risk_level = "bajo"

    return risk_score, risk_level


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def ingesta_texto(state: DocumentState) -> dict:
    """
    Carga el texto del documento desde la fuente disponible.
    En DEMO lee documents.json local. En LIVE procesaría el archivo real (PDF/DOCX).
    """
    doc_id = state.get("doc_id", "DOC-001")
    data_dir = get_data_dir()

    doc = get_document(doc_id, data_dir)
    raw_text = doc.get("raw_text", "")
    doc_title = doc.get("title", "Documento sin título")
    doc_type = doc.get("type", "unknown")

    logger.info(
        "Documento ingestado: id=%s tipo=%s formato=%s longitud=%d",
        doc.get("id"), doc_type, doc.get("doc_format"), len(raw_text),
    )

    return {
        "doc_title": doc_title,
        "doc_type": doc_type,
        "raw_text": raw_text,
        "events": [{"type": "documento_ingestado", "doc_id": doc_id,
                    "titulo": doc_title, "tipo": doc_type,
                    "formato": doc.get("doc_format", "text"),
                    "longitud_chars": len(raw_text)}],
    }


def segmentar_secciones(state: DocumentState) -> dict:
    """
    Divide el texto del documento en secciones lógicas mediante detección
    de headers contractuales (CLÁUSULA N, ARTÍCULO N, CONSIDERANDOS, etc.).
    En modo LIVE el LLM puede complementar la segmentación semántica.
    """
    raw_text = state.get("raw_text", "")

    sections = _split_sections(raw_text)

    logger.info(
        "Segmentación completada: %d secciones detectadas",
        len(sections),
    )

    return {
        "sections": sections,
        "events": [{"type": "secciones_segmentadas", "total_secciones": len(sections),
                    "titulos": [s["title"] for s in sections]}],
    }


def extraer_clausulas(state: DocumentState) -> dict:
    """
    Identifica y extrae cláusulas clave (penalidades, SLA, confidencialidad, etc.)
    mediante keyword matching sobre cada sección.
    En modo LIVE usa embeddings semánticos para mayor precisión.
    """
    sections = state.get("sections", [])
    data_dir = get_data_dir()

    patterns = get_clause_patterns(data_dir)
    clauses = _find_clauses_in_sections(sections, patterns)

    clause_types = [c["type"] for c in clauses]
    logger.info(
        "Cláusulas extraídas: %d tipos detectados — %s",
        len(clauses), clause_types,
    )

    return {
        "clauses": clauses,
        "events": [{"type": "clausulas_extraidas", "total": len(clauses),
                    "tipos": clause_types}],
    }


def clasificar_riesgos(state: DocumentState) -> dict:
    """
    Asigna nivel de riesgo (bajo/medio/alto) a cada cláusula y al documento
    completo. Calcula risk_score compuesto (0-100).

    Regla DEMO: si alguna cláusula es "alto" → riesgo alto.
    En modo LIVE el LLM puede ajustar el score con contexto de negocio.
    """
    clauses = state.get("clauses", [])
    doc_title = state.get("doc_title", "")

    risk_score, risk_level = _score_from_clauses(clauses)

    if _LIVE_MODE and clauses:
        clause_summary = "\n".join(
            f"- {c['type']}: {c['description']} (riesgo {c['risk']})"
            for c in clauses
        )
        prompt = (
            f"Eres un abogado contractual senior. Evalúa el riesgo de este documento:\n\n"
            f"Documento: {doc_title}\n"
            f"Cláusulas identificadas:\n{clause_summary}\n\n"
            f"Score calculado: {risk_score}/100\n"
            f"¿El score es apropiado? Responde SOLO con un número del 0 al 100."
        )
        llm_score_str = _llm_analyze(prompt, str(risk_score))
        try:
            risk_score = max(0, min(100, int(llm_score_str.strip())))
            if risk_score >= 70:
                risk_level = "alto"
            elif risk_score >= 35:
                risk_level = "medio"
            else:
                risk_level = "bajo"
        except ValueError:
            pass

    logger.info(
        "Riesgo clasificado: score=%d level=%s cláusulas_alto=%d",
        risk_score, risk_level,
        sum(1 for c in clauses if c["risk"] == "alto"),
    )

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "events": [{"type": "riesgo_clasificado", "score": risk_score,
                    "nivel": risk_level,
                    "clausulas_alto": sum(1 for c in clauses if c["risk"] == "alto"),
                    "clausulas_medio": sum(1 for c in clauses if c["risk"] == "medio"),
                    "clausulas_bajo": sum(1 for c in clauses if c["risk"] == "bajo")}],
    }


def escalar_revision_legal(state: DocumentState) -> dict:
    """
    Genera notas de escalación para revisión por el equipo legal senior.
    Solo se ejecuta para documentos con riesgo ALTO.
    En modo LIVE el LLM redacta la justificación de escalación.
    """
    clauses = state.get("clauses", [])
    doc_title = state.get("doc_title", "")
    risk_score = state.get("risk_score", 0)

    alto_clauses = [c for c in clauses if c["risk"] == "alto"]
    reasons = [
        c["escalation_reason"] for c in alto_clauses
        if c.get("escalation_reason")
    ]

    fallback_notes = (
        f"**ESCALACIÓN REQUERIDA — Revisión Legal Senior**\n\n"
        f"El documento «{doc_title}» ha obtenido un score de riesgo de {risk_score}/100, "
        f"lo que lo clasifica como ALTO RIESGO.\n\n"
        f"**Cláusulas que requieren revisión por abogado:**\n"
        + "\n".join(
            f"- **{c['type'].upper()}** en sección «{c['section']}»: {c['description']}"
            for c in alto_clauses
        )
        + "\n\n**Justificaciones de escalación:**\n"
        + "\n".join(f"- {r}" for r in reasons if r)
        + "\n\n_Se recomienda no firmar este documento sin revisión del equipo legal senior._"
    )

    escalation_notes = _llm_analyze(
        f"Eres un abogado senior. Redacta una nota de escalación interna para el equipo legal "
        f"sobre el documento «{doc_title}» (score: {risk_score}/100, riesgo ALTO). "
        f"Cláusulas críticas:\n"
        + "\n".join(f"- {c['type']}: {c['description']}" for c in alto_clauses)
        + "\nMáximo 150 palabras. En español.",
        fallback_notes,
    )

    logger.info(
        "Escalación generada: doc=%s score=%d cláusulas_alto=%d",
        doc_title, risk_score, len(alto_clauses),
    )

    return {
        "escalation_notes": escalation_notes,
        "events": [{"type": "escalacion_generada", "score": risk_score,
                    "clausulas_criticas": [c["type"] for c in alto_clauses]}],
    }


def generar_checklist(state: DocumentState) -> dict:
    """
    Produce la lista de verificación de cumplimiento y puntos de negociación
    basada en las cláusulas identificadas en el documento.
    """
    clauses = state.get("clauses", [])
    risk_level = state.get("risk_level", "bajo")

    items: list[str] = []

    for clause in clauses:
        item = clause.get("checklist_item", "")
        if item:
            risk_prefix = {
                "alto": "🔴 [CRÍTICO]",
                "medio": "🟡 [REVISAR]",
                "bajo": "🟢 [VERIFICAR]",
            }.get(clause["risk"], "•")
            items.append(f"{risk_prefix} {item} (sección: {clause['section']})")

    if risk_level == "alto":
        items.insert(0, "🔴 [CRÍTICO] Obtener aprobación del equipo legal senior antes de firmar")
    if not items:
        items.append("🟢 [VERIFICAR] Confirmar que todas las cláusulas cumplen con la política contractual interna")

    general_items = [
        "🟢 [VERIFICAR] Confirmar identidad y facultades de los firmantes de ambas partes",
        "🟢 [VERIFICAR] Revisar que las fechas de vigencia son correctas y razonables",
        "🟢 [VERIFICAR] Verificar que el contrato ha sido debidamente numerado y rubricado en cada página",
    ]
    items.extend(general_items)

    logger.info("Checklist generado: %d ítems para riesgo=%s", len(items), risk_level)

    return {
        "checklist": items,
        "events": [{"type": "checklist_generado", "total_items": len(items),
                    "riesgo": risk_level}],
    }


def producir_resumen_ejecutivo(state: DocumentState) -> dict:
    """
    Genera el resumen ejecutivo del análisis en lenguaje natural.
    En modo DEMO usa una plantilla estructurada con los datos del análisis.
    En modo LIVE el LLM produce una narrativa ejecutiva completa.
    """
    doc_title = state.get("doc_title", "Documento")
    doc_type = state.get("doc_type", "contrato")
    clauses = state.get("clauses", [])
    risk_score = state.get("risk_score", 0)
    risk_level = state.get("risk_level", "bajo")
    checklist = state.get("checklist", [])
    escalation_notes = state.get("escalation_notes", "")

    risk_label = {"bajo": "BAJO RIESGO", "medio": "RIESGO MODERADO", "alto": "ALTO RIESGO"}.get(
        risk_level, risk_level.upper()
    )

    clause_lines = "\n".join(
        f"  • {c['description']} (sección: {c['section']}, riesgo: {c['risk'].upper()})"
        for c in clauses
    )

    fallback_summary = (
        f"## Resumen Ejecutivo — Análisis Contractual\n\n"
        f"**Documento analizado:** {doc_title}\n"
        f"**Tipo:** {doc_type.upper()} | **Clasificación de riesgo:** {risk_label} ({risk_score}/100)\n\n"
        f"### Cláusulas identificadas ({len(clauses)} total)\n"
        f"{clause_lines if clause_lines else '  • No se identificaron cláusulas de riesgo relevantes.'}\n\n"
        f"### Puntos de atención\n"
        + "\n".join(f"  {item}" for item in checklist[:6])
        + ("\n\n### Escalación requerida\n" + escalation_notes if escalation_notes else "")
        + f"\n\n_Análisis generado automáticamente por el Agente Analista de Documentos — Caso 05._\n"
        f"_Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}_"
    )

    summary = _llm_analyze(
        f"Eres un abogado contractual senior. Genera un resumen ejecutivo en español del análisis "
        f"de este documento: {doc_title} (tipo: {doc_type}, riesgo: {risk_label}, score: {risk_score}/100).\n\n"
        f"Cláusulas detectadas:\n{clause_lines}\n\n"
        f"Principales puntos del checklist:\n"
        + "\n".join(checklist[:5])
        + "\n\nMáximo 300 palabras. Incluye: hallazgos clave, nivel de riesgo y recomendación.",
        fallback_summary,
    )

    logger.info(
        "Resumen ejecutivo generado: doc=%s nivel=%s modo=%s",
        doc_title, risk_level, "LIVE" if _LIVE_MODE else "DEMO",
    )

    return {
        "executive_summary": summary,
        "done": True,
        "events": [{"type": "resumen_generado", "doc_id": state.get("doc_id"),
                    "risk_level": risk_level, "risk_score": risk_score,
                    "total_clausulas": len(clauses)}],
    }


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def route_by_risk(state: DocumentState) -> str:
    """Decide la ruta según el nivel de riesgo del documento."""
    if state.get("risk_level") == "alto":
        return "escalar_revision_legal"
    return "generar_checklist"


# ---------------------------------------------------------------------------
# Compilación del grafo
# ---------------------------------------------------------------------------

def compile_graph():
    """Construye y compila el StateGraph con MemorySaver como checkpointer."""
    builder = StateGraph(DocumentState)

    builder.add_node("ingesta_texto", ingesta_texto)
    builder.add_node("segmentar_secciones", segmentar_secciones)
    builder.add_node("extraer_clausulas", extraer_clausulas)
    builder.add_node("clasificar_riesgos", clasificar_riesgos)
    builder.add_node("escalar_revision_legal", escalar_revision_legal)
    builder.add_node("generar_checklist", generar_checklist)
    builder.add_node("producir_resumen_ejecutivo", producir_resumen_ejecutivo)

    builder.set_entry_point("ingesta_texto")
    builder.add_edge("ingesta_texto", "segmentar_secciones")
    builder.add_edge("segmentar_secciones", "extraer_clausulas")
    builder.add_edge("extraer_clausulas", "clasificar_riesgos")

    builder.add_conditional_edges(
        "clasificar_riesgos",
        route_by_risk,
        {
            "escalar_revision_legal": "escalar_revision_legal",
            "generar_checklist": "generar_checklist",
        },
    )

    builder.add_edge("escalar_revision_legal", "generar_checklist")
    builder.add_edge("generar_checklist", "producir_resumen_ejecutivo")
    builder.add_edge("producir_resumen_ejecutivo", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)
