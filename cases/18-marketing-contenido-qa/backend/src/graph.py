"""
graph.py — Grafo LangGraph para el Caso 18: Marketing de Contenido con QA.

Pipeline con dos loops de revisión condicional (tope de iteraciones):

  parsear_brief → generar_borrador
       → revisar_estilo_marca
            ├─ estilo.ok=False ∧ iter<max → reescribir_tono → revisar_estilo_marca
            └─ ok → verificar_hechos
       → verificar_hechos
            ├─ hechos.ok=False ∧ iter<max → corregir_hechos → verificar_hechos
            └─ ok → optimizar_seo
       → optimizar_seo → aprobacion_editor → publicar_contenido → producir_resumen → END

DEMO: redacción y QA deterministas a partir de brand_style.json y fact_sources.json
(sin LLM, sin red). LIVE opt-in con OPENAI_API_KEY para resumen ejecutivo.
"""
from __future__ import annotations

import logging
import operator
import os
import re
from datetime import datetime
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import get_brand_style, get_brief, get_fact_sources, get_quality_rules
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class MarketingState(TypedDict):
    brief_id: str
    brief: dict
    borrador: str
    estilo: dict
    hechos: dict
    seo: dict
    iter_estilo: int
    iter_hechos: int
    alucinaciones_retiradas_total: int
    hechos_inyectados_total: int
    score_global: int
    riesgo: str
    decision_editor: str
    contenido_final: str
    diff: dict
    metricas: dict
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


def _palabras(texto: str) -> list:
    return re.findall(r"\b[\wáéíóúñÁÉÍÓÚÑ]+\b", texto.lower())


def _frases(texto: str) -> list:
    return [f.strip() for f in re.split(r"[.!?]+", texto) if f.strip()]


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def parsear_brief(state: MarketingState) -> dict:
    brief_id = state.get("brief_id", "BR-001")
    brief = get_brief(brief_id, get_data_dir())

    logger.info(
        "Brief parseado: id=%s formato=%s tono=%s keywords=%d hechos=%d",
        brief_id, brief.get("formato"), brief.get("tono"),
        len(brief.get("keywords", [])), len(brief.get("hechos_obligatorios", [])),
    )

    return {
        "brief": brief,
        "iter_estilo": 0,
        "iter_hechos": 0,
        "events": [{
            "type": "brief_parseado",
            "brief_id": brief_id,
            "titulo": brief.get("titulo"),
            "formato": brief.get("formato"),
            "audiencia": brief.get("audiencia"),
            "tono": brief.get("tono"),
            "keywords": brief.get("keywords", []),
            "hechos_obligatorios": len(brief.get("hechos_obligatorios", [])),
        }],
    }


def _render_borrador(brief: dict) -> str:
    """Genera un borrador determinista según el formato del brief.

    Incluye intencionalmente los `claims_riesgosos` del brief (que serán
    detectados como alucinaciones por verificar_hechos) y los `hechos_obligatorios`
    (verificados contra fact_sources).
    """
    formato = brief.get("formato", "blog_post")
    titulo = brief.get("titulo", "(sin título)")
    audiencia = brief.get("audiencia", "general")
    keywords = brief.get("keywords", [])
    hechos = [h.get("claim", "") for h in brief.get("hechos_obligatorios", [])]
    riesgosos = brief.get("claims_riesgosos", [])

    kws = ", ".join(keywords) if keywords else "—"
    hechos_md = "\n".join(f"- {c}" for c in hechos) if hechos else "- (sin hechos clave)"
    riesgosos_md = "\n".join(f"- {c}" for c in riesgosos) if riesgosos else ""

    if formato == "email":
        head = f"# Asunto: {titulo}\n\nHola equipo,\n\n"
        cta = "\n\nSolicita una demo aquí.\n"
    elif formato == "landing":
        head = f"# {titulo}\n\n## Para {audiencia}\n\n"
        cta = "\n\nAgenda una sesión con nuestro equipo.\n"
    else:  # blog_post
        head = f"# {titulo}\n\n_Audiencia: {audiencia}_\n\n"
        cta = "\n\nComienza tu prueba hoy.\n"

    cuerpo = (
        f"En este contenido revisamos los puntos clave alrededor de: {kws}.\n\n"
        f"### Lo que necesitas saber\n{hechos_md}\n\n"
    )
    if riesgosos_md:
        cuerpo += f"### Mensajes destacados\n{riesgosos_md}\n\n"

    return head + cuerpo + cta


def generar_borrador(state: MarketingState) -> dict:
    brief = state.get("brief", {})
    borrador = _render_borrador(brief)
    palabras = len(_palabras(borrador))

    logger.info(
        "Borrador generado: formato=%s palabras=%d",
        brief.get("formato"), palabras,
    )

    return {
        "borrador": borrador,
        "events": [{
            "type": "borrador_generado",
            "formato": brief.get("formato"),
            "palabras": palabras,
            "longitud_objetivo": brief.get("longitud_objetivo_palabras", 0),
        }],
    }


def revisar_estilo_marca(state: MarketingState) -> dict:
    """Detecta palabras prohibidas, palabras no preferidas y frases demasiado largas."""
    rules = get_quality_rules(get_data_dir())
    style = get_brand_style(get_data_dir())
    pen = rules.get("penalizaciones", {})
    umbral = rules.get("umbral_estilo", 80)

    borrador = state.get("borrador", "")
    texto_low = borrador.lower()

    prohibidas = style.get("palabras_prohibidas", [])
    preferidas = style.get("palabras_preferidas", {})
    limites = style.get("limites_estilo", {})
    max_frase = limites.get("longitud_frase_max_palabras", 28)

    issues: list = []
    score = 100

    for p in prohibidas:
        if p.lower() in texto_low:
            score -= pen.get("palabra_prohibida", 12)
            issues.append({
                "tipo": "palabra_prohibida",
                "ref": p,
                "mensaje": f"La palabra '{p}' no está alineada con la voz de marca.",
            })

    for orig, _ in preferidas.items():
        if re.search(rf"\b{re.escape(orig)}\b", texto_low):
            score -= pen.get("palabra_no_preferida", 4)
            issues.append({
                "tipo": "palabra_no_preferida",
                "ref": orig,
                "mensaje": f"Usar la alternativa preferida en lugar de '{orig}'.",
            })

    frases_largas = 0
    for f in _frases(borrador):
        if len(_palabras(f)) > max_frase:
            frases_largas += 1
    if frases_largas:
        score -= pen.get("frase_demasiado_larga", 5) * frases_largas
        issues.append({
            "tipo": "frase_demasiado_larga",
            "ref": f"{frases_largas} frase(s)",
            "mensaje": f"Hay {frases_largas} frase(s) con más de {max_frase} palabras.",
        })

    score = max(score, 0)
    ok = score >= umbral and not any(i["tipo"] == "palabra_prohibida" for i in issues)
    iter_estilo = state.get("iter_estilo", 0)

    logger.info(
        "QA estilo iter=%d: score=%d issues=%d ok=%s",
        iter_estilo, score, len(issues), ok,
    )

    return {
        "estilo": {"score": score, "issues": issues, "ok": ok},
        "events": [{
            "type": "estilo_revisado",
            "iter": iter_estilo,
            "score": score,
            "issues": len(issues),
            "ok": ok,
        }],
    }


def reescribir_tono(state: MarketingState) -> dict:
    """Elimina palabras prohibidas, sustituye no preferidas e incrementa iter."""
    style = get_brand_style(get_data_dir())
    borrador = state.get("borrador", "")
    prohibidas = style.get("palabras_prohibidas", [])
    preferidas = style.get("palabras_preferidas", {})

    nuevo = borrador
    for p in prohibidas:
        # Reemplaza la palabra prohibida con un placeholder neutro (case-insensitive).
        nuevo = re.sub(re.escape(p), "[—]", nuevo, flags=re.IGNORECASE)
    for orig, alt in preferidas.items():
        nuevo = re.sub(rf"\b{re.escape(orig)}\b", alt, nuevo, flags=re.IGNORECASE)

    iter_estilo = state.get("iter_estilo", 0) + 1
    logger.info("Tono reescrito: iter=%d", iter_estilo)

    return {
        "borrador": nuevo,
        "iter_estilo": iter_estilo,
        "events": [{"type": "tono_reescrito", "iter": iter_estilo}],
    }


def estilo_router(state: MarketingState) -> Literal["reescribir_tono", "verificar_hechos"]:
    rules = get_quality_rules(get_data_dir())
    max_iter = rules.get("max_iter_estilo", 2)
    estilo = state.get("estilo", {})
    if not estilo.get("ok", False) and state.get("iter_estilo", 0) < max_iter:
        return "reescribir_tono"
    return "verificar_hechos"


def verificar_hechos(state: MarketingState) -> dict:
    """Verifica que cada hecho obligatorio aparezca y detecta alucinaciones.

    Una alucinación = una frase del borrador que se parece a una claim no
    respaldada por ninguna fuente (registrada en `claims_riesgosos` del brief).
    """
    rules = get_quality_rules(get_data_dir())
    fact_sources = get_fact_sources(get_data_dir())
    pen = rules.get("penalizaciones", {})
    umbral = rules.get("umbral_hechos", 90)

    brief = state.get("brief", {})
    borrador = state.get("borrador", "")
    texto_low = borrador.lower()

    issues: list = []
    score = 100

    # 1. Falta de hechos obligatorios
    hechos_faltantes = []
    for h in brief.get("hechos_obligatorios", []):
        claim = h.get("claim", "")
        source_id = h.get("source_id", "")
        verificado = (
            claim.lower() in texto_low
            and source_id in fact_sources
            and claim in fact_sources[source_id].get("claims_verificados", [])
        )
        if not verificado:
            hechos_faltantes.append(h["id"])
            score -= pen.get("falta_hecho_obligatorio", 10)
            issues.append({
                "tipo": "falta_hecho_obligatorio",
                "ref": h["id"],
                "mensaje": f"El hecho {h['id']} no aparece o no está respaldado por fuente.",
            })

    # 2. Alucinaciones / claims no verificables
    alucinaciones = []
    todas_claims_verificadas = {
        c.lower() for src in fact_sources.values()
        for c in src.get("claims_verificados", [])
    }
    for claim_riesgoso in brief.get("claims_riesgosos", []):
        if claim_riesgoso.lower() in texto_low:
            if claim_riesgoso.lower() not in todas_claims_verificadas:
                alucinaciones.append(claim_riesgoso)
                score -= pen.get("alucinacion_detectada", 22)
                issues.append({
                    "tipo": "alucinacion_detectada",
                    "ref": claim_riesgoso[:60],
                    "mensaje": "Afirmación sin respaldo en fuentes autorizadas.",
                })

    score = max(score, 0)
    ok = score >= umbral and not alucinaciones
    iter_hechos = state.get("iter_hechos", 0)

    logger.info(
        "QA hechos iter=%d: score=%d alucinaciones=%d faltantes=%d ok=%s",
        iter_hechos, score, len(alucinaciones), len(hechos_faltantes), ok,
    )

    return {
        "hechos": {
            "score": score,
            "issues": issues,
            "alucinaciones": alucinaciones,
            "faltantes": hechos_faltantes,
            "ok": ok,
        },
        "events": [{
            "type": "hechos_verificados",
            "iter": iter_hechos,
            "score": score,
            "alucinaciones": len(alucinaciones),
            "faltantes": len(hechos_faltantes),
            "ok": ok,
        }],
    }


def corregir_hechos(state: MarketingState) -> dict:
    """Elimina alucinaciones e inyecta los hechos obligatorios faltantes."""
    brief = state.get("brief", {})
    fact_sources = get_fact_sources(get_data_dir())
    borrador = state.get("borrador", "")
    hechos = state.get("hechos", {})

    nuevo = borrador
    # Quita alucinaciones (reemplazo por nota neutra)
    for claim in hechos.get("alucinaciones", []):
        nuevo = nuevo.replace(claim, "[afirmación retirada por falta de respaldo]")

    # Agrega hechos faltantes al final, citando la fuente
    bloque_faltantes = []
    for h in brief.get("hechos_obligatorios", []):
        if h["id"] in hechos.get("faltantes", []):
            src = fact_sources.get(h.get("source_id", ""), {})
            bloque_faltantes.append(
                f"- {h['claim']} _(fuente: {src.get('titulo', h.get('source_id'))})_"
            )
    if bloque_faltantes:
        nuevo += "\n\n### Datos verificados (inyectados)\n" + "\n".join(bloque_faltantes) + "\n"

    iter_hechos = state.get("iter_hechos", 0) + 1
    retiradas = len(hechos.get("alucinaciones", []))
    inyectadas = len(bloque_faltantes)
    total_retiradas = state.get("alucinaciones_retiradas_total", 0) + retiradas
    total_inyectadas = state.get("hechos_inyectados_total", 0) + inyectadas
    logger.info("Hechos corregidos: iter=%d retiradas=%d inyectadas=%d",
                iter_hechos, retiradas, inyectadas)

    return {
        "borrador": nuevo,
        "iter_hechos": iter_hechos,
        "alucinaciones_retiradas_total": total_retiradas,
        "hechos_inyectados_total": total_inyectadas,
        "events": [{
            "type": "hechos_corregidos",
            "iter": iter_hechos,
            "retiradas": retiradas,
            "inyectadas": inyectadas,
        }],
    }


def hechos_router(state: MarketingState) -> Literal["corregir_hechos", "optimizar_seo"]:
    rules = get_quality_rules(get_data_dir())
    max_iter = rules.get("max_iter_hechos", 2)
    hechos = state.get("hechos", {})
    if not hechos.get("ok", False) and state.get("iter_hechos", 0) < max_iter:
        return "corregir_hechos"
    return "optimizar_seo"


def optimizar_seo(state: MarketingState) -> dict:
    """Calcula densidad de keywords, presencia de H1 y CTA."""
    rules = get_quality_rules(get_data_dir())
    seo_rules = rules.get("seo", {})
    pen = rules.get("penalizaciones", {})

    brief = state.get("brief", {})
    style = get_brand_style(get_data_dir())
    borrador = state.get("borrador", "")
    palabras = _palabras(borrador)
    total = max(len(palabras), 1)

    keywords = brief.get("keywords", [])
    densidades = {}
    keywords_ausentes = []
    score = 100
    issues: list = []

    for kw in keywords:
        kw_low = kw.lower()
        ocurrencias = sum(1 for w in palabras if kw_low == w) + borrador.lower().count(kw_low) - sum(1 for w in palabras if kw_low == w)
        # ocurrencias de la frase (incluye multi-palabra)
        ocurrencias = borrador.lower().count(kw_low)
        densidad_pct = round(ocurrencias / total * 100, 2)
        densidades[kw] = densidad_pct
        if ocurrencias == 0:
            keywords_ausentes.append(kw)
            score -= pen.get("keyword_ausente", 6)
            issues.append({
                "tipo": "keyword_ausente",
                "ref": kw,
                "mensaje": f"La keyword '{kw}' no aparece en el contenido.",
            })

    if not borrador.lstrip().startswith("# "):
        score -= pen.get("sin_h1", 5)
        issues.append({"tipo": "sin_h1", "ref": "—", "mensaje": "Falta encabezado H1 al inicio."})

    cta_recom = style.get("cta_recomendados", [])
    if cta_recom and not any(c.lower() in borrador.lower() for c in cta_recom):
        score -= pen.get("sin_cta", 8)
        issues.append({"tipo": "sin_cta", "ref": "—", "mensaje": "Falta CTA reconocible."})

    score = max(score, 0)

    logger.info(
        "SEO optimizado: score=%d kw_ausentes=%d densidades=%s",
        score, len(keywords_ausentes), densidades,
    )

    return {
        "seo": {
            "score": score,
            "densidades_pct": densidades,
            "keywords_ausentes": keywords_ausentes,
            "issues": issues,
        },
        "events": [{
            "type": "seo_optimizado",
            "score": score,
            "keywords_ausentes": keywords_ausentes,
        }],
    }


def aprobacion_editor(state: MarketingState) -> dict:
    """Calcula score global y decisión editorial determinista."""
    rules = get_quality_rules(get_data_dir())
    umbrales = rules.get("umbral_riesgo", {"verde_min_score": 88, "amarillo_min_score": 70})

    estilo = state.get("estilo", {}).get("score", 0)
    hechos = state.get("hechos", {}).get("score", 0)
    seo = state.get("seo", {}).get("score", 0)
    # Pesos: hechos > estilo > seo
    score_global = round(hechos * 0.5 + estilo * 0.3 + seo * 0.2)

    if score_global >= umbrales["verde_min_score"]:
        riesgo, decision = "verde", "aprobado"
    elif score_global >= umbrales["amarillo_min_score"]:
        riesgo, decision = "amarillo", "aprobado_con_observaciones"
    else:
        riesgo, decision = "rojo", "rechazado"

    logger.info(
        "Editor: score_global=%d riesgo=%s decision=%s",
        score_global, riesgo, decision,
    )

    return {
        "score_global": score_global,
        "riesgo": riesgo,
        "decision_editor": decision,
        "events": [{
            "type": "editor_decidio",
            "score_global": score_global,
            "riesgo": riesgo,
            "decision": decision,
        }],
    }


def publicar_contenido(state: MarketingState) -> dict:
    borrador = state.get("borrador", "")
    brief = state.get("brief", {})
    decision = state.get("decision_editor", "")

    encabezado = (
        f"<!-- Generado por agente de marketing · {_now_iso()} · "
        f"brief={brief.get('id','')} decision={decision} -->\n\n"
    )
    contenido_final = encabezado + borrador

    diff = {
        "palabras_finales": len(_palabras(contenido_final)),
        "lineas": contenido_final.count("\n"),
        "iter_estilo": state.get("iter_estilo", 0),
        "iter_hechos": state.get("iter_hechos", 0),
        "alucinaciones_retiradas": state.get("alucinaciones_retiradas_total", 0),
        "hechos_inyectados": state.get("hechos_inyectados_total", 0),
    }

    metricas = {
        "score_global": state.get("score_global", 0),
        "score_estilo": state.get("estilo", {}).get("score", 0),
        "score_hechos": state.get("hechos", {}).get("score", 0),
        "score_seo": state.get("seo", {}).get("score", 0),
        "iter_estilo": state.get("iter_estilo", 0),
        "iter_hechos": state.get("iter_hechos", 0),
        "palabras_finales": diff["palabras_finales"],
        "decision_editor": decision,
        "riesgo": state.get("riesgo", ""),
    }

    logger.info(
        "Contenido publicado: palabras=%d iter_estilo=%d iter_hechos=%d",
        diff["palabras_finales"], diff["iter_estilo"], diff["iter_hechos"],
    )

    return {
        "contenido_final": contenido_final,
        "diff": diff,
        "metricas": metricas,
        "events": [{
            "type": "contenido_publicado",
            "palabras": diff["palabras_finales"],
            "diff": diff,
        }],
    }


def producir_resumen(state: MarketingState) -> dict:
    metricas = state.get("metricas", {})
    brief = state.get("brief", {})
    score = state.get("score_global", 0)
    riesgo = state.get("riesgo", "")
    riesgo_label = {"verde": "BAJO", "amarillo": "MEDIO", "rojo": "ALTO"}.get(riesgo, riesgo.upper())
    decision = state.get("decision_editor", "")

    fallback = (
        f"## Resumen — Contenido para **{brief.get('titulo','(sin título)')}**\n\n"
        f"**Score global:** {score}/100 · **Riesgo:** {riesgo_label} · "
        f"**Decisión editor:** {decision}\n\n"
        f"### Métricas\n"
        f"- Score estilo: {metricas.get('score_estilo', 0)}\n"
        f"- Score hechos: {metricas.get('score_hechos', 0)}\n"
        f"- Score SEO: {metricas.get('score_seo', 0)}\n"
        f"- Iter. tono: {metricas.get('iter_estilo', 0)}\n"
        f"- Iter. hechos: {metricas.get('iter_hechos', 0)}\n"
        f"- Palabras finales: {metricas.get('palabras_finales', 0)}\n\n"
        f"### Próximos pasos\n"
        f"- Publicar en el CMS según calendario editorial.\n"
        f"- Revisar la pieza si hubo alucinaciones detectadas.\n\n"
        f"_Generado por agente de marketing · Caso 18. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres editor jefe de marketing. Redacta un resumen ejecutivo en español "
            f"(máx 150 palabras) sobre la pieza '{brief.get('titulo')}' "
            f"(score {score}/100, riesgo {riesgo_label}, decisión: {decision}, "
            f"{metricas.get('iter_estilo',0)} iter. de tono, "
            f"{metricas.get('iter_hechos',0)} iter. de hechos). "
            f"Cierra con próximos pasos concretos."
        )
        resumen = _llm_invoke(prompt, fallback)
    else:
        resumen = fallback

    logger.info(
        "Resumen generado: brief=%s score=%s riesgo=%s modo=%s",
        brief.get("id"), score, riesgo, "LIVE" if _LIVE_MODE else "DEMO",
    )

    return {
        "resumen": resumen,
        "done": True,
        "events": [{
            "type": "marketing_completado",
            "brief": brief.get("id"),
            "score": score,
            "riesgo": riesgo,
            "decision": decision,
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(MarketingState)

    builder.add_node("parsear_brief", parsear_brief)
    builder.add_node("generar_borrador", generar_borrador)
    builder.add_node("revisar_estilo_marca", revisar_estilo_marca)
    builder.add_node("reescribir_tono", reescribir_tono)
    builder.add_node("verificar_hechos", verificar_hechos)
    builder.add_node("corregir_hechos", corregir_hechos)
    builder.add_node("optimizar_seo", optimizar_seo)
    builder.add_node("aprobacion_editor", aprobacion_editor)
    builder.add_node("publicar_contenido", publicar_contenido)
    builder.add_node("producir_resumen", producir_resumen)

    builder.set_entry_point("parsear_brief")
    builder.add_edge("parsear_brief", "generar_borrador")
    builder.add_edge("generar_borrador", "revisar_estilo_marca")

    builder.add_conditional_edges(
        "revisar_estilo_marca",
        estilo_router,
        {
            "reescribir_tono": "reescribir_tono",
            "verificar_hechos": "verificar_hechos",
        },
    )
    builder.add_edge("reescribir_tono", "revisar_estilo_marca")

    builder.add_conditional_edges(
        "verificar_hechos",
        hechos_router,
        {
            "corregir_hechos": "corregir_hechos",
            "optimizar_seo": "optimizar_seo",
        },
    )
    builder.add_edge("corregir_hechos", "verificar_hechos")

    builder.add_edge("optimizar_seo", "aprobacion_editor")
    builder.add_edge("aprobacion_editor", "publicar_contenido")
    builder.add_edge("publicar_contenido", "producir_resumen")
    builder.add_edge("producir_resumen", END)

    return builder.compile(checkpointer=MemorySaver())
