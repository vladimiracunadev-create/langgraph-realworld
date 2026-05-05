"""
graph.py — Grafo LangGraph para el Caso 08: Ventas B2B + CRM.

Pipeline comercial de outbound automatizado:
  investigar_cuenta → calificar_lead → [router score_icp]
    ├─ no_califica → descartar_y_registrar ─────────────────────┐
    └─ califica → personalizar_outreach                          │
                       ↓                                          │
                  seleccionar_canal                               │
                       ↓                                          │
                  simular_envio                                   │
                       ↓                                          │
                  monitorear_respuesta                            │
                       ↓                                          │
                  [router señal_interes]                          │
                       ├─ negativo → descartar_y_registrar ──────┤
                       ├─ sin_respuesta → programar_followup ────┤
                       └─ positivo → escalar_ejecutivo ──────────┤
                                                                  ↓
                                                          actualizar_crm
                                                                  ↓
                                                          producir_resumen → END

Modo DEMO (sin OPENAI_API_KEY): scoring ICP + plantillas deterministas.
Modo LIVE (con OPENAI_API_KEY): GPT-4o-mini personaliza el mensaje de outreach
y redacta el resumen ejecutivo.
"""
from __future__ import annotations

import logging
import operator
import os
from datetime import date, timedelta
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import (
    get_account,
    get_icp,
    get_responses,
    get_sales_reps,
    get_templates,
    render_template,
)
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado del grafo
# ---------------------------------------------------------------------------

class B2BSalesState(TypedDict):
    account_id: str
    company_name: str
    industria: str
    industria_tag: str
    tamano_empresa: str
    pais: str
    web: str
    contacto_principal: dict
    enriquecimiento: dict
    icp_score: int
    icp_nivel: str
    icp_razones: list
    califica: bool
    mensaje_outreach: dict
    canal: str
    cadencia: list
    envio: dict
    respuesta_prospect: dict
    senal_interes: str
    siguiente_accion: str
    crm_record: dict
    resumen_comercial: str
    events: Annotated[list, operator.add]
    done: bool


# ---------------------------------------------------------------------------
# Helper LLM
# ---------------------------------------------------------------------------

def _llm_invoke(prompt: str, fallback: str) -> str:
    if not _LIVE_MODE:
        return fallback
    try:
        from langchain_openai import ChatOpenAI  # noqa: PLC0415
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model_name, temperature=0.3)
        return llm.invoke(prompt).content
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM no disponible, fallback DEMO: %s", exc)
        return fallback


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def investigar_cuenta(state: B2BSalesState) -> dict:
    """Carga la cuenta y enriquece sus datos públicos (DEMO: lee accounts.json)."""
    account_id = state.get("account_id", "ACC-001")
    data_dir = get_data_dir()

    acc = get_account(account_id, data_dir)
    enriquecimiento = {
        "tecnologias": acc.get("tecnologias_detectadas", []),
        "noticias_recientes": acc.get("noticias_recientes", []),
        "headcount": acc.get("headcount", 0),
        "revenue_estimado_usd": acc.get("revenue_estimado_usd", 0),
        "pain_points_publicos": acc.get("pain_points_publicos", []),
        "señales_compra": acc.get("señales_compra", []),
    }

    logger.info(
        "Cuenta investigada: %s industria=%s tamaño=%s headcount=%d",
        acc.get("company_name"), acc.get("industria_tag"),
        acc.get("tamano_empresa"), enriquecimiento["headcount"],
    )

    return {
        "company_name": acc.get("company_name", ""),
        "industria": acc.get("industria", ""),
        "industria_tag": acc.get("industria_tag", ""),
        "tamano_empresa": acc.get("tamano_empresa", ""),
        "pais": acc.get("pais", ""),
        "web": acc.get("web", ""),
        "contacto_principal": acc.get("contacto_principal", {}),
        "enriquecimiento": enriquecimiento,
        "events": [{
            "type": "cuenta_investigada",
            "company": acc.get("company_name"),
            "industria": acc.get("industria_tag"),
            "tamano": acc.get("tamano_empresa"),
            "headcount": enriquecimiento["headcount"],
            "tecnologias_detectadas": len(enriquecimiento["tecnologias"]),
            "señales_compra": len(enriquecimiento["señales_compra"]),
        }],
    }


def calificar_lead(state: B2BSalesState) -> dict:
    """
    Calcula el score ICP combinando industria, tamaño, modernidad del stack
    tecnológico, noticias recientes y señales de compra activas.
    """
    icp = get_icp(get_data_dir())
    enr = state.get("enriquecimiento", {})
    industria = state.get("industria_tag", "")
    tamano = state.get("tamano_empresa", "")

    score = 0
    razones: list[str] = []

    industria_score = icp.get("industrias_prioritarias", {}).get(industria, 0)
    score += industria_score
    if industria_score >= 25:
        razones.append(f"Industria '{industria}' es prioritaria en el ICP (+{industria_score}).")
    elif industria_score >= 15:
        razones.append(f"Industria '{industria}' tiene fit medio en el ICP (+{industria_score}).")
    else:
        razones.append(icp.get("razones_descarte_comunes", {}).get("industria_no_objetivo", "Industria no objetivo."))

    headcount = enr.get("headcount", 0)
    minimo = icp.get("tamano_minimo_empleados", 50)
    if headcount < minimo:
        razones.append(icp.get("razones_descarte_comunes", {}).get("tamano_insuficiente", "Tamaño insuficiente."))
    else:
        tamano_score = icp.get("tamano_optimo", {}).get(tamano, 0)
        score += tamano_score
        if tamano_score >= 20:
            razones.append(f"Tamaño '{tamano}' óptimo para el ICP (+{tamano_score}).")

    modern = set(t.lower() for t in icp.get("tech_stack_modern", []))
    detectadas = set(t.lower() for t in enr.get("tecnologias", []))
    overlap = modern & detectadas
    if overlap:
        score += icp.get("tech_stack_modern_score", 15)
        razones.append(f"Stack moderno detectado: {', '.join(sorted(overlap))[:80]} (+{icp.get('tech_stack_modern_score', 15)}).")
    else:
        razones.append(icp.get("razones_descarte_comunes", {}).get("stack_legacy", "Stack legacy."))

    señales = enr.get("señales_compra", [])
    if señales:
        s_score = min(len(señales) * icp.get("señales_compra_score_por_item", 8), 24)
        score += s_score
        razones.append(f"{len(señales)} señales activas de compra (+{s_score}).")
    else:
        razones.append(icp.get("razones_descarte_comunes", {}).get("sin_señales", "Sin señales activas."))

    noticias = enr.get("noticias_recientes", [])
    if noticias:
        n_score = min(len(noticias) * icp.get("noticias_relevantes_score_por_item", 4), icp.get("max_noticias_score", 12))
        score += n_score

    bloqueo_publico = any("no procurement" in n.lower() or "freeze" in n.lower() for n in noticias)
    if bloqueo_publico:
        razones.append(icp.get("razones_descarte_comunes", {}).get("ventana_no_disponible", "Ventana no disponible."))
        score = max(score - 25, 0)

    score = max(0, min(score, 100))

    umbrales = icp.get("umbrales_nivel", {})
    if score >= umbrales.get("alto", 70):
        nivel = "alto"
    elif score >= umbrales.get("medio", 50):
        nivel = "medio"
    elif score >= umbrales.get("bajo", 30):
        nivel = "bajo"
    else:
        nivel = "fuera_icp"

    califica = score >= icp.get("umbral_califica", 50)

    logger.info(
        "Lead calificado: company=%s score=%d nivel=%s califica=%s",
        state.get("company_name"), score, nivel, califica,
    )

    return {
        "icp_score": score,
        "icp_nivel": nivel,
        "icp_razones": razones,
        "califica": califica,
        "events": [{
            "type": "lead_calificado",
            "score": score,
            "nivel": nivel,
            "califica": califica,
            "razones": razones[:4],
        }],
    }


def descartar_y_registrar(state: B2BSalesState) -> dict:
    """Descarta la cuenta del pipeline y registra la razón en el CRM."""
    razones = state.get("icp_razones", [])
    senal = state.get("senal_interes", "")
    if senal == "negativo":
        motivo = "Respuesta negativa del prospect — congelar 90 días y reabrir."
    else:
        motivo = "No califica para el ICP actual — fuera de target."

    logger.info(
        "Cuenta descartada: %s motivo=%s",
        state.get("company_name"), motivo,
    )

    return {
        "siguiente_accion": "descartar",
        "events": [{
            "type": "cuenta_descartada",
            "motivo": motivo,
            "razones_principales": razones[:3],
        }],
    }


def personalizar_outreach(state: B2BSalesState) -> dict:
    """Genera el mensaje personalizado según industria y enriquecimiento."""
    industria = state.get("industria_tag", "default")
    contacto = state.get("contacto_principal", {})
    enr = state.get("enriquecimiento", {})
    company = state.get("company_name", "")

    templates = get_templates(get_data_dir())
    template = templates.get(industria, templates.get("default", {}))

    pain_point = (enr.get("pain_points_publicos") or ["optimización operativa"])[0]
    tech_observado = ", ".join(enr.get("tecnologias", [])[:2]) or "el stack actual"
    benchmark_por_industria = {
        "logistics": "TransGlobal Cargo",
        "fintech": "BancoMéxico Digital",
        "media": "PixelHeart Games",
        "saas": "Datalink SaaS",
    }
    benchmark = benchmark_por_industria.get(industria, "un cliente comparable")

    variables = {
        "company_name": company,
        "contacto_nombre": contacto.get("nombre", "[contacto]").split()[0] if contacto.get("nombre") else "[contacto]",
        "rep_nombre": "Camila Saavedra",
        "pain_point": pain_point,
        "tech_observado": tech_observado,
        "benchmark": benchmark,
        "industria": state.get("industria", ""),
    }

    asunto = render_template(template.get("asunto", ""), variables)
    cuerpo = render_template(template.get("cuerpo", ""), variables)
    cta = render_template(template.get("cta", ""), variables)

    if _LIVE_MODE:
        prompt = (
            f"Eres un AE B2B senior. Mejora la redacción del siguiente correo de outreach a "
            f"{contacto.get('rol', '')} de {company} ({state.get('industria', '')}). "
            f"Mantén el tono consultivo, sin corporativismo, máximo 130 palabras. "
            f"No inventes datos. Responde SOLO con el cuerpo del correo en español.\n\n"
            f"BORRADOR ACTUAL:\n{cuerpo}"
        )
        cuerpo = _llm_invoke(prompt, cuerpo)

    mensaje = {
        "asunto": asunto,
        "cuerpo": cuerpo,
        "cta": cta,
        "idioma": template.get("idioma", "es"),
    }

    logger.info(
        "Outreach personalizado: company=%s template=%s longitud=%d",
        company, industria, len(cuerpo),
    )

    return {
        "mensaje_outreach": mensaje,
        "events": [{
            "type": "outreach_personalizado",
            "template_usado": industria,
            "longitud_chars": len(cuerpo),
            "asunto": asunto[:80],
        }],
    }


def seleccionar_canal(state: B2BSalesState) -> dict:
    """
    Selecciona canal y arma cadencia. Reglas:
    - C-level / VP -> email + LinkedIn (toques 1, 4, 8 días).
    - Otros roles  -> email solamente (toques 1, 5).
    """
    rol = (state.get("contacto_principal", {}) or {}).get("rol", "").lower()
    es_clevel = any(k in rol for k in ["chief", "ceo", "coo", "cto", "cfo", "vp", "vicepresidente", "director"])

    if es_clevel:
        canal = "email+linkedin"
        cadencia = [
            {"step": 1, "dias": 0, "canal": "email"},
            {"step": 2, "dias": 4, "canal": "linkedin"},
            {"step": 3, "dias": 8, "canal": "email"},
        ]
    else:
        canal = "email"
        cadencia = [
            {"step": 1, "dias": 0, "canal": "email"},
            {"step": 2, "dias": 5, "canal": "email"},
        ]

    logger.info(
        "Canal seleccionado: company=%s canal=%s steps=%d",
        state.get("company_name"), canal, len(cadencia),
    )

    return {
        "canal": canal,
        "cadencia": cadencia,
        "events": [{
            "type": "canal_seleccionado",
            "canal": canal,
            "es_clevel": es_clevel,
            "total_steps": len(cadencia),
        }],
    }


def simular_envio(state: B2BSalesState) -> dict:
    """Simula el envío del primer toque de la cadencia (DEMO)."""
    cadencia = state.get("cadencia", [])
    primer_toque = cadencia[0] if cadencia else {"step": 1, "canal": "email"}

    envio = {
        "timestamp": date.today().isoformat() + "T09:30:00Z",
        "canal": primer_toque.get("canal"),
        "step": primer_toque.get("step", 1),
        "status": "delivered",
        "tracking_pixel": True,
    }

    logger.info(
        "Envío simulado: company=%s canal=%s step=%d",
        state.get("company_name"), envio["canal"], envio["step"],
    )

    return {
        "envio": envio,
        "events": [{
            "type": "envio_simulado",
            "canal": envio["canal"],
            "step": envio["step"],
            "status": envio["status"],
        }],
    }


def monitorear_respuesta(state: B2BSalesState) -> dict:
    """Lee la respuesta simulada del prospect (DEMO determinista)."""
    account_id = state.get("account_id", "")
    responses = get_responses(get_data_dir())
    resp = responses.get(account_id, {
        "tipo": "sin_respuesta",
        "fragmento": "Sin actividad registrada.",
        "intent_score": 20,
    })

    tipo = resp.get("tipo", "sin_respuesta")
    if tipo not in {"positivo", "negativo", "sin_respuesta", "no_aplica"}:
        tipo = "sin_respuesta"

    senal = "sin_respuesta" if tipo == "no_aplica" else tipo

    logger.info(
        "Respuesta monitoreada: company=%s tipo=%s intent_score=%d",
        state.get("company_name"), senal, resp.get("intent_score", 0),
    )

    return {
        "respuesta_prospect": resp,
        "senal_interes": senal,
        "events": [{
            "type": "respuesta_monitoreada",
            "tipo": senal,
            "intent_score": resp.get("intent_score", 0),
            "tiempo_respuesta_horas": resp.get("tiempo_respuesta_horas"),
        }],
    }


def programar_followup(state: B2BSalesState) -> dict:
    """Calcula el siguiente toque y queda en estado nurturing."""
    cadencia = state.get("cadencia", [])
    siguiente = cadencia[1] if len(cadencia) > 1 else {"step": 2, "dias": 5, "canal": "email"}
    fecha_proximo = (date.today() + timedelta(days=siguiente.get("dias", 5))).isoformat()

    accion = (
        f"Follow-up programado: {siguiente.get('canal')} en {siguiente.get('dias')} días "
        f"({fecha_proximo}) — step {siguiente.get('step')}."
    )

    logger.info(
        "Followup programado: company=%s fecha=%s",
        state.get("company_name"), fecha_proximo,
    )

    return {
        "siguiente_accion": accion,
        "events": [{
            "type": "followup_programado",
            "fecha_proximo_toque": fecha_proximo,
            "canal": siguiente.get("canal"),
            "step": siguiente.get("step"),
        }],
    }


def escalar_ejecutivo(state: B2BSalesState) -> dict:
    """Asigna AE por industria/país y prioridad por menor carga."""
    industria_tag = state.get("industria_tag", "")
    pais = state.get("pais", "")
    reps = get_sales_reps(get_data_dir())

    candidatos = [
        r for r in reps
        if industria_tag in r.get("industrias", []) and (not pais or pais in r.get("paises", []))
    ]
    if not candidatos:
        candidatos = [r for r in reps if industria_tag in r.get("industrias", [])]
    if not candidatos:
        candidatos = reps

    elegido = sorted(candidatos, key=lambda r: r.get("deals_activos", 999))[0] if candidatos else {
        "id": "AE-DEMO", "nombre": "AE DEMO", "rol": "Account Executive",
        "email": "ae@miempresa.com", "industrias": [], "paises": [],
        "deals_activos": 0, "carga": "baja", "quota_pct": 0,
    }

    accion = (
        f"Reunión solicitada por el prospect — handoff a {elegido.get('nombre')} "
        f"con SLA de respuesta en 4 horas hábiles."
    )

    logger.info(
        "Ejecutivo escalado: company=%s ae=%s deals_activos=%d",
        state.get("company_name"), elegido.get("nombre"),
        elegido.get("deals_activos", 0),
    )

    return {
        "siguiente_accion": accion,
        "events": [{
            "type": "ejecutivo_escalado",
            "ae": elegido.get("nombre"),
            "deals_activos": elegido.get("deals_activos", 0),
            "carga": elegido.get("carga"),
            "industrias": elegido.get("industrias", []),
        }],
        "crm_record": {
            "ae_assigned": elegido,
        },
    }


def actualizar_crm(state: B2BSalesState) -> dict:
    """Determina deal_stage final y consolida el record CRM."""
    senal = state.get("senal_interes", "")
    califica = state.get("califica", False)
    base = state.get("crm_record", {}) or {}

    if not califica:
        stage = "Disqualified"
    elif senal == "positivo":
        stage = "Meeting Scheduled"
    elif senal == "negativo":
        stage = "Closed Lost"
    elif senal == "sin_respuesta":
        stage = "Nurturing"
    else:
        stage = "Prospecting"

    notes = []
    if state.get("icp_razones"):
        notes.append("ICP score: " + str(state.get("icp_score", 0)) + "/100 — " + state["icp_razones"][0])
    if state.get("respuesta_prospect", {}).get("fragmento"):
        notes.append("Última señal: " + state["respuesta_prospect"]["fragmento"][:160])

    crm_record = {
        **base,
        "deal_stage": stage,
        "company": state.get("company_name", ""),
        "contact_email": (state.get("contacto_principal", {}) or {}).get("email", ""),
        "icp_nivel": state.get("icp_nivel", ""),
        "icp_score": state.get("icp_score", 0),
        "industria": state.get("industria_tag", ""),
        "pais": state.get("pais", ""),
        "next_step": state.get("siguiente_accion", ""),
        "notes": notes,
        "updated_at": date.today().isoformat(),
    }

    logger.info(
        "CRM actualizado: company=%s stage=%s icp=%d",
        state.get("company_name"), stage, state.get("icp_score", 0),
    )

    return {
        "crm_record": crm_record,
        "events": [{
            "type": "crm_actualizado",
            "deal_stage": stage,
            "icp_nivel": state.get("icp_nivel", ""),
            "next_step": state.get("siguiente_accion", "")[:120],
        }],
    }


def producir_resumen(state: B2BSalesState) -> dict:
    """Resumen ejecutivo para el sales manager."""
    company = state.get("company_name", "")
    industria = state.get("industria", "")
    score = state.get("icp_score", 0)
    nivel = state.get("icp_nivel", "")
    senal = state.get("senal_interes", "")
    crm = state.get("crm_record", {})
    accion = state.get("siguiente_accion", "")

    fallback = (
        f"## Resumen comercial — {company}\n\n"
        f"**Industria:** {industria}\n"
        f"**ICP score:** {score}/100 — nivel {nivel.upper()}\n"
        f"**Señal del prospect:** {senal}\n"
        f"**Deal stage CRM:** {crm.get('deal_stage', 'N/D')}\n\n"
        f"### Próxima acción\n{accion}\n\n"
        f"### Notas\n"
        + "\n".join(f"- {n}" for n in crm.get("notes", []))
        + f"\n\n_Generado por agente B2B — Caso 08. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres VP de Ventas. Redacta en español un resumen ejecutivo (máx. 200 palabras) "
            f"para el sales manager sobre la cuenta {company} ({industria}). "
            f"ICP score: {score}/100. Señal: {senal}. Stage: {crm.get('deal_stage')}. "
            f"Próxima acción: {accion}. Sé directo y orientado a decisión."
        )
        resumen = _llm_invoke(prompt, fallback)
    else:
        resumen = fallback

    logger.info(
        "Resumen comercial generado: company=%s stage=%s modo=%s",
        company, crm.get("deal_stage"), "LIVE" if _LIVE_MODE else "DEMO",
    )

    return {
        "resumen_comercial": resumen,
        "done": True,
        "events": [{
            "type": "resumen_generado",
            "company": company,
            "deal_stage": crm.get("deal_stage", ""),
        }],
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

def route_by_icp(state: B2BSalesState) -> str:
    return "personalizar_outreach" if state.get("califica") else "descartar_y_registrar"


def route_by_senal(state: B2BSalesState) -> str:
    senal = state.get("senal_interes", "")
    if senal == "positivo":
        return "escalar_ejecutivo"
    if senal == "negativo":
        return "descartar_y_registrar"
    return "programar_followup"


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(B2BSalesState)

    builder.add_node("investigar_cuenta", investigar_cuenta)
    builder.add_node("calificar_lead", calificar_lead)
    builder.add_node("descartar_y_registrar", descartar_y_registrar)
    builder.add_node("personalizar_outreach", personalizar_outreach)
    builder.add_node("seleccionar_canal", seleccionar_canal)
    builder.add_node("simular_envio", simular_envio)
    builder.add_node("monitorear_respuesta", monitorear_respuesta)
    builder.add_node("programar_followup", programar_followup)
    builder.add_node("escalar_ejecutivo", escalar_ejecutivo)
    builder.add_node("actualizar_crm", actualizar_crm)
    builder.add_node("producir_resumen", producir_resumen)

    builder.set_entry_point("investigar_cuenta")
    builder.add_edge("investigar_cuenta", "calificar_lead")

    builder.add_conditional_edges(
        "calificar_lead",
        route_by_icp,
        {
            "personalizar_outreach": "personalizar_outreach",
            "descartar_y_registrar": "descartar_y_registrar",
        },
    )
    builder.add_edge("personalizar_outreach", "seleccionar_canal")
    builder.add_edge("seleccionar_canal", "simular_envio")
    builder.add_edge("simular_envio", "monitorear_respuesta")

    builder.add_conditional_edges(
        "monitorear_respuesta",
        route_by_senal,
        {
            "escalar_ejecutivo": "escalar_ejecutivo",
            "descartar_y_registrar": "descartar_y_registrar",
            "programar_followup": "programar_followup",
        },
    )
    builder.add_edge("escalar_ejecutivo", "actualizar_crm")
    builder.add_edge("programar_followup", "actualizar_crm")
    builder.add_edge("descartar_y_registrar", "actualizar_crm")
    builder.add_edge("actualizar_crm", "producir_resumen")
    builder.add_edge("producir_resumen", END)

    return builder.compile(checkpointer=MemorySaver())
