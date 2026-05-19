"""
graph.py — Grafo LangGraph para el Caso 24: Asistente de Product Manager.

Pipeline:
  clarificar_problema → definir_epica → descomponer_historias → estimar_complejidad
    → priorizar_backlog → crear_tickets → asignar_sprint → monitorear_progreso
    → estado_sprint_router
         ├─ impedimento → escalar_impedimento → generar_reporte_estado → END
         ├─ normal      → generar_reporte_estado → END
         └─ completado  → retrospectiva_y_metricas → generar_reporte_estado → END

DEMO: ejecución determinista. LIVE opt-in con OPENAI_API_KEY sólo para el reporte
ejecutivo final.
"""
from __future__ import annotations

import hashlib
import logging
import operator
import os
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import (
    get_catalogo_estimacion,
    get_equipo,
    get_iniciativa,
    get_policy,
)
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class PMState(TypedDict):
    iniciativa_id: str
    iniciativa: dict
    preguntas_clarificadoras: list
    respuestas_clarificadoras: list
    epica: dict
    historias: list
    estimaciones: dict
    backlog_priorizado: list
    tickets_creados: list
    sprint_asignado: dict
    progreso_sprint: dict
    impedimentos: list
    estado_sprint: str
    reporte: str
    retrospectiva: dict
    estado_final: str
    metricas: dict
    audit_trail: list
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


def _short_hash(*parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return h[:6].upper()


# Preguntas clarificadoras por fuente
_PREGUNTAS_POR_FUENTE = {
    "idea": [
        "¿Qué problema concreto resuelve esta idea?",
        "¿Qué métrica esperamos mover y en qué magnitud?",
        "¿Qué segmento de usuarios la usaría primero?",
    ],
    "feedback": [
        "¿Cuántos usuarios han pedido esto?",
        "¿Qué workaround usan hoy y qué fricción tiene?",
        "¿Hay un patrón en los planes/segmentos que lo solicitan?",
    ],
    "requerimiento": [
        "¿Qué stakeholder lo solicitó y por qué ahora?",
        "¿Cuál es el criterio de éxito acordado?",
        "¿Existen restricciones técnicas o de compliance?",
    ],
}


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def clarificar_problema(state: PMState) -> dict:
    iniciativa_id = state.get("iniciativa_id", "I-001")
    iniciativa = get_iniciativa(iniciativa_id, get_data_dir())
    fuente = iniciativa.get("fuente", "idea")
    preguntas = _PREGUNTAS_POR_FUENTE.get(fuente, _PREGUNTAS_POR_FUENTE["idea"])
    respuestas = [
        f"(DEMO) Respuesta sintética para iniciativa {iniciativa_id} - pregunta {i+1}"
        for i in range(len(preguntas))
    ]

    logger.info(
        "Problema clarificado: iniciativa=%s fuente=%s preguntas=%d",
        iniciativa_id, fuente, len(preguntas),
    )

    return {
        "iniciativa": iniciativa,
        "preguntas_clarificadoras": preguntas,
        "respuestas_clarificadoras": respuestas,
        "audit_trail": [{"step": "clarificar_problema", "iniciativa_id": iniciativa_id}],
        "events": [{
            "type": "problema_clarificado",
            "iniciativa_id": iniciativa_id,
            "fuente": fuente,
            "preguntas": len(preguntas),
        }],
    }


def definir_epica(state: PMState) -> dict:
    iniciativa = state.get("iniciativa", {})
    titulo = iniciativa.get("titulo", "")
    contexto = iniciativa.get("contexto", "")
    stakeholders = iniciativa.get("stakeholders", [])

    epica = {
        "id": "EP-" + iniciativa.get("id", "").replace("I-", ""),
        "titulo": f"Épica: {titulo}",
        "objetivo": f"Entregar {titulo} para resolver: {contexto}",
        "criterios_aceptacion": [
            f"Todos los stakeholders ({', '.join(stakeholders)}) validan el alcance",
            "Las historias asociadas pasan QA y staging",
            "La métrica de éxito definida muestra mejora medible",
        ],
        "metricas_exito": [
            {"nombre": "adopcion_pct", "objetivo": 30},
            {"nombre": "satisfaccion_usuarios", "objetivo": 4.0},
        ],
    }

    logger.info("Épica definida: %s (%d criterios)", epica["id"], len(epica["criterios_aceptacion"]))

    return {
        "epica": epica,
        "audit_trail": [{"step": "definir_epica", "epica_id": epica["id"]}],
        "events": [{"type": "epica_definida", "epica_id": epica["id"], "titulo": epica["titulo"]}],
    }


def descomponer_historias(state: PMState) -> dict:
    iniciativa = state.get("iniciativa", {})
    raw = iniciativa.get("historias", [])
    formato = get_policy(get_data_dir()).get("formato_historia", "Como ... quiero ... para ...")

    historias = []
    for h in raw:
        texto = f"Como {h.get('como','')} quiero {h.get('quiero','')} para {h.get('para','')}"
        historias.append({
            "id": h.get("id", ""),
            "como": h.get("como", ""),
            "quiero": h.get("quiero", ""),
            "para": h.get("para", ""),
            "complejidad": h.get("complejidad", "M"),
            "acceptance_criteria": h.get("acceptance_criteria", []),
            "texto": texto,
            "formato": formato,
        })

    logger.info("Historias descompuestas: %d para iniciativa=%s", len(historias), iniciativa.get("id"))

    return {
        "historias": historias,
        "audit_trail": [{"step": "descomponer_historias", "n": len(historias)}],
        "events": [{
            "type": "historias_descompuestas",
            "iniciativa_id": iniciativa.get("id"),
            "n_historias": len(historias),
        }],
    }


def estimar_complejidad(state: PMState) -> dict:
    catalogo = get_catalogo_estimacion(get_data_dir())
    estimaciones: dict = {}
    for h in state.get("historias", []):
        comp = h.get("complejidad", "M")
        puntos = catalogo.get(comp, {}).get("puntos", 5)
        estimaciones[h["id"]] = puntos

    logger.info("Estimaciones calculadas: %s", estimaciones)

    return {
        "estimaciones": estimaciones,
        "audit_trail": [{"step": "estimar_complejidad", "total_puntos": sum(estimaciones.values())}],
        "events": [{
            "type": "complejidad_estimada",
            "total_puntos": sum(estimaciones.values()),
            "n": len(estimaciones),
        }],
    }


def priorizar_backlog(state: PMState) -> dict:
    iniciativa = state.get("iniciativa", {})
    historias = state.get("historias", [])
    estimaciones = state.get("estimaciones", {})
    valor_negocio = iniciativa.get("valor_negocio", 50)

    enriquecidas = []
    for h in historias:
        enriquecidas.append({
            **h,
            "puntos": estimaciones.get(h["id"], 5),
            "valor_negocio": valor_negocio,
        })

    # Ordenar por (valor_negocio desc, puntos asc)
    backlog = sorted(enriquecidas, key=lambda x: (-x["valor_negocio"], x["puntos"]))

    logger.info("Backlog priorizado: %d historias", len(backlog))

    return {
        "backlog_priorizado": backlog,
        "audit_trail": [{"step": "priorizar_backlog", "n": len(backlog)}],
        "events": [{
            "type": "backlog_priorizado",
            "n": len(backlog),
            "primera": backlog[0]["id"] if backlog else None,
        }],
    }


def crear_tickets(state: PMState) -> dict:
    policy = get_policy(get_data_dir())
    sistema = policy.get("sistema_tickets", "JiraDemo")
    prefijo = policy.get("prefijo_ticket", "PROJ")
    iniciativa = state.get("iniciativa", {})
    backlog = state.get("backlog_priorizado", [])

    tickets = []
    for idx, h in enumerate(backlog, start=1):
        # ID determinista por iniciativa+historia
        suffix = _short_hash(iniciativa.get("id", ""), h["id"])
        ticket_id = f"{prefijo}-{suffix}"
        tickets.append({
            "id": ticket_id,
            "sistema": sistema,
            "url": f"https://{sistema.lower()}.demo/browse/{ticket_id}",
            "historia_id": h["id"],
            "titulo": h["texto"],
            "puntos": h["puntos"],
            "orden": idx,
        })

    logger.info("Tickets creados: %d en sistema=%s", len(tickets), sistema)

    return {
        "tickets_creados": tickets,
        "audit_trail": [{"step": "crear_tickets", "n": len(tickets), "sistema": sistema}],
        "events": [{
            "type": "tickets_creados",
            "n": len(tickets),
            "sistema": sistema,
        }],
    }


def asignar_sprint(state: PMState) -> dict:
    policy = get_policy(get_data_dir())
    iniciativa = state.get("iniciativa", {})
    equipo = get_equipo(iniciativa.get("equipo_id", ""), get_data_dir())
    capacidad_equipo = equipo.get("capacidad_puntos", 15)
    cap_policy = policy.get("max_puntos_sprint_por_equipo", 15)
    capacidad = min(capacidad_equipo, cap_policy)

    backlog = state.get("backlog_priorizado", [])
    asignadas: list = []
    fuera: list = []
    acumulado = 0

    for h in backlog:
        puntos = h["puntos"]
        if acumulado + puntos <= capacidad:
            asignadas.append(h)
            acumulado += puntos
        else:
            fuera.append(h)

    sprint = {
        "sprint_id": f"S-{iniciativa.get('id','').replace('I-','')}-01",
        "equipo_id": equipo.get("id", ""),
        "capacidad": capacidad,
        "puntos_asignados": acumulado,
        "historias_asignadas": [h["id"] for h in asignadas],
        "fuera_de_capacidad": [h["id"] for h in fuera],
    }

    logger.info(
        "Sprint asignado: %s capacidad=%d asignados=%d fuera=%d",
        sprint["sprint_id"], capacidad, acumulado, len(fuera),
    )

    return {
        "sprint_asignado": sprint,
        "audit_trail": [{"step": "asignar_sprint", "sprint_id": sprint["sprint_id"]}],
        "events": [{
            "type": "sprint_asignado",
            "sprint_id": sprint["sprint_id"],
            "puntos_asignados": acumulado,
            "fuera_de_capacidad": len(fuera),
        }],
    }


def monitorear_progreso(state: PMState) -> dict:
    iniciativa = state.get("iniciativa", {})
    progreso = iniciativa.get("progreso_sprint", {})
    impedimentos = iniciativa.get("impedimentos", [])
    policy = get_policy(get_data_dir())
    umbral = policy.get("umbral_impedimento_dias", 2)

    total = sum(progreso.values()) if progreso else 0
    hechas = progreso.get("hecho", 0)
    bloqueadas = progreso.get("bloqueado", 0)

    # Determinar estado_sprint
    impedimentos_criticos = [
        i for i in impedimentos if i.get("dias_abierto", 0) >= umbral
    ]
    if total > 0 and hechas == total and not impedimentos_criticos:
        estado_sprint = "completado"
    elif impedimentos_criticos or bloqueadas > 0:
        estado_sprint = "impedimento"
    else:
        estado_sprint = "normal"

    logger.info(
        "Progreso monitoreado: total=%d hechas=%d bloqueadas=%d estado=%s",
        total, hechas, bloqueadas, estado_sprint,
    )

    return {
        "progreso_sprint": progreso,
        "impedimentos": impedimentos,
        "estado_sprint": estado_sprint,
        "audit_trail": [{"step": "monitorear_progreso", "estado_sprint": estado_sprint}],
        "events": [{
            "type": "progreso_monitoreado",
            "estado_sprint": estado_sprint,
            "hechas": hechas,
            "bloqueadas": bloqueadas,
            "impedimentos_criticos": len(impedimentos_criticos),
        }],
    }


def estado_sprint_router(
    state: PMState,
) -> Literal["escalar_impedimento", "generar_reporte_estado", "retrospectiva_y_metricas"]:
    estado = state.get("estado_sprint", "normal")
    if estado == "impedimento":
        return "escalar_impedimento"
    if estado == "completado":
        return "retrospectiva_y_metricas"
    return "generar_reporte_estado"


def escalar_impedimento(state: PMState) -> dict:
    policy = get_policy(get_data_dir())
    canal = policy.get("slack_channel_impedimentos", "#pm-bloqueos")
    impedimentos = state.get("impedimentos", [])

    notificaciones = []
    for imp in impedimentos:
        notificaciones.append({
            "canal": canal,
            "mensaje": (
                f"Impedimento {imp.get('id','?')} abierto hace {imp.get('dias_abierto',0)} días: "
                f"{imp.get('descripcion','')} (responsable: {imp.get('responsable','—')})"
            ),
        })

    logger.info("Impedimentos escalados: %d notificaciones a %s", len(notificaciones), canal)

    return {
        "audit_trail": [{"step": "escalar_impedimento", "n": len(notificaciones), "canal": canal}],
        "events": [{
            "type": "impedimento_escalado",
            "canal": canal,
            "n_notificaciones": len(notificaciones),
            "notificaciones": notificaciones,
        }],
    }


def retrospectiva_y_metricas(state: PMState) -> dict:
    sprint = state.get("sprint_asignado", {})
    progreso = state.get("progreso_sprint", {})
    puntos_planificados = sprint.get("puntos_asignados", 0)
    # Asume que cada historia "hecha" contribuye proporcionalmente
    n_total = sum(progreso.values()) if progreso else 0
    n_hechas = progreso.get("hecho", 0)

    if n_total > 0:
        puntos_hechos = round(puntos_planificados * (n_hechas / n_total), 2)
    else:
        puntos_hechos = 0

    velocidad = puntos_hechos
    predictibilidad = round(puntos_hechos / puntos_planificados, 2) if puntos_planificados else 0.0

    retro = {
        "velocidad": velocidad,
        "puntos_planificados": puntos_planificados,
        "puntos_hechos": puntos_hechos,
        "predictibilidad": predictibilidad,
        "accion_items": [
            "Mantener el ritmo: el sprint cerró al 100%",
            "Revisar story splitting para el próximo sprint",
        ],
    }

    logger.info(
        "Retrospectiva: velocidad=%s predictibilidad=%s", velocidad, predictibilidad,
    )

    return {
        "retrospectiva": retro,
        "audit_trail": [{"step": "retrospectiva_y_metricas", "predictibilidad": predictibilidad}],
        "events": [{
            "type": "retrospectiva_calculada",
            "velocidad": velocidad,
            "predictibilidad": predictibilidad,
        }],
    }


def generar_reporte_estado(state: PMState) -> dict:
    iniciativa = state.get("iniciativa", {})
    epica = state.get("epica", {})
    sprint = state.get("sprint_asignado", {})
    progreso = state.get("progreso_sprint", {})
    estado = state.get("estado_sprint", "normal")
    retro = state.get("retrospectiva", {})
    impedimentos = state.get("impedimentos", [])

    metricas = {
        "iniciativa_id": iniciativa.get("id"),
        "epica_id": epica.get("id"),
        "sprint_id": sprint.get("sprint_id"),
        "n_historias": len(state.get("historias", [])),
        "n_tickets": len(state.get("tickets_creados", [])),
        "puntos_asignados": sprint.get("puntos_asignados", 0),
        "fuera_de_capacidad": len(sprint.get("fuera_de_capacidad", [])),
        "estado_sprint": estado,
        "impedimentos_abiertos": len(impedimentos),
    }

    fallback = (
        f"## Reporte de estado — {iniciativa.get('titulo','')}\n\n"
        f"**Iniciativa:** {iniciativa.get('id','')} · "
        f"**Épica:** {epica.get('id','')} · "
        f"**Sprint:** {sprint.get('sprint_id','')}\n\n"
        f"**Estado del sprint:** {estado}\n"
        f"**Puntos asignados:** {sprint.get('puntos_asignados',0)} / capacidad {sprint.get('capacidad',0)}\n"
        f"**Historias fuera de capacidad:** {len(sprint.get('fuera_de_capacidad', []))}\n"
        f"**Progreso:** {progreso}\n"
        f"**Impedimentos abiertos:** {len(impedimentos)}\n"
    )
    if retro:
        fallback += (
            f"\n### Retrospectiva\n"
            f"- Velocidad: {retro.get('velocidad',0)} pts\n"
            f"- Predictibilidad: {retro.get('predictibilidad',0)}\n"
        )
    fallback += (
        f"\n_Generado por agente PM · Caso 24. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres Product Manager senior. Redacta en español (máx 150 palabras) un "
            f"reporte de estado del sprint {sprint.get('sprint_id','')} de la iniciativa "
            f"{iniciativa.get('titulo','')} con estado '{estado}' y métricas {metricas}."
        )
        reporte = _llm_invoke(prompt, fallback)
    else:
        reporte = fallback

    estado_final = (
        "sprint_completado" if estado == "completado"
        else "sprint_con_impedimento" if estado == "impedimento"
        else "sprint_en_curso"
    )

    return {
        "reporte": reporte,
        "estado_final": estado_final,
        "metricas": metricas,
        "done": True,
        "audit_trail": [{"step": "generar_reporte_estado", "estado_final": estado_final}],
        "events": [{
            "type": "reporte_generado",
            "estado_final": estado_final,
            "iniciativa_id": iniciativa.get("id"),
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(PMState)

    builder.add_node("clarificar_problema", clarificar_problema)
    builder.add_node("definir_epica", definir_epica)
    builder.add_node("descomponer_historias", descomponer_historias)
    builder.add_node("estimar_complejidad", estimar_complejidad)
    builder.add_node("priorizar_backlog", priorizar_backlog)
    builder.add_node("crear_tickets", crear_tickets)
    builder.add_node("asignar_sprint", asignar_sprint)
    builder.add_node("monitorear_progreso", monitorear_progreso)
    builder.add_node("escalar_impedimento", escalar_impedimento)
    builder.add_node("retrospectiva_y_metricas", retrospectiva_y_metricas)
    builder.add_node("generar_reporte_estado", generar_reporte_estado)

    builder.set_entry_point("clarificar_problema")
    builder.add_edge("clarificar_problema", "definir_epica")
    builder.add_edge("definir_epica", "descomponer_historias")
    builder.add_edge("descomponer_historias", "estimar_complejidad")
    builder.add_edge("estimar_complejidad", "priorizar_backlog")
    builder.add_edge("priorizar_backlog", "crear_tickets")
    builder.add_edge("crear_tickets", "asignar_sprint")
    builder.add_edge("asignar_sprint", "monitorear_progreso")

    builder.add_conditional_edges(
        "monitorear_progreso",
        estado_sprint_router,
        {
            "escalar_impedimento": "escalar_impedimento",
            "generar_reporte_estado": "generar_reporte_estado",
            "retrospectiva_y_metricas": "retrospectiva_y_metricas",
        },
    )

    builder.add_edge("escalar_impedimento", "generar_reporte_estado")
    builder.add_edge("retrospectiva_y_metricas", "generar_reporte_estado")
    builder.add_edge("generar_reporte_estado", END)

    return builder.compile(checkpointer=MemorySaver())
