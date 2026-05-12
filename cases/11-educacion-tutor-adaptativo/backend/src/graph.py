"""
graph.py — Grafo LangGraph para el Caso 11: Tutor Adaptativo.

Pipeline IRT simplificado de tutoría personalizada:

  cargar_perfil → {router diagnostico}
                    ├─ sin_diagnostico → aplicar_diagnostico ┐
                    └─ con_diagnostico ────────────────────── ┴→ seleccionar_item
                                                                     ↓
                       ┌──────────────────────────────────────────── presentar_actividad
                       │                                                 ↓
                       │                                            evaluar_respuesta
                       │                                                 ↓
                       │                                       {router desempeño}
                       │                  ┌────────────────┬─────────────┴──────────────┐
                       │            domina │     error_conceptual │           frustracion │
                       │                   ↓                       ↓                     ↓
                       │          aumentar_dificultad   remediar_concepto    reducir_dificultad
                       │                   └──────────┬────────────┴────────────┬─────────┘
                       │                              ↓                          │
                       │                     {router continuar}                  │
                       │                       ├─ continuar ──────────── ───┐  │
                       └───────────────────────┘                            └──┘
                                                  ↓ finalizar
                                          actualizar_perfil → producir_reporte → END

Modelo de habilidad: escala 1.0–10.0. Cada ítem tiene `dificultad` y `concepto`.
Simulador determinista (per-student seed) decide entre:
  - correcto (domina): gap ≤ tolerancia
  - error_conceptual: tolerancia < gap < umbral_frustracion
  - frustracion: gap ≥ umbral_frustracion o errores_consecutivos ≥ umbral

LIVE opt-in con OPENAI_API_KEY para retroalimentación enriquecida y reporte ejecutivo.
"""
from __future__ import annotations

import logging
import operator
import os
import random
from datetime import datetime
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import get_item_bank, get_policy, get_student
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class TutorState(TypedDict):
    student_id: str
    student: dict
    policy: dict
    diagnostico_aplicado: bool
    habilidad: float
    habilidad_inicial: float
    max_items: int
    items_disponibles: list
    items_servidos: list
    current_item: dict
    evaluacion_actual: dict
    evaluaciones: list
    conceptos_dominados: list
    conceptos_a_remediar: list
    errores_consecutivos: int
    ajuste_ultimo: str
    perfil_final: dict
    reporte: str
    events: Annotated[list, operator.add]
    done: bool


# ---------------------------------------------------------------------------
# LLM helper
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


# ---------------------------------------------------------------------------
# Helpers puros
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _simulate_response(
    item: dict,
    habilidad: float,
    policy: dict,
    errores_consecutivos: int,
    rng: random.Random,
) -> dict:
    """
    Decide de forma determinista (por seed) la respuesta del estudiante simulado.

    Resultado:
      - "correcto"          : domina el ítem
      - "error_conceptual"  : confunde, pero recuperable con remediación
      - "frustracion"       : ítem muy por encima del nivel, o racha de errores
    """
    tolerancia = float(policy.get("tolerancia_dominio", 0.5))
    umbral_error = float(policy.get("umbral_error_conceptual", 2.0))
    umbral_frus = float(policy.get("umbral_frustracion", 3.5))
    errores_max = int(policy.get("errores_consecutivos_frustracion", 2))

    dificultad = float(item.get("dificultad", 5.0))
    gap = dificultad - habilidad

    if errores_consecutivos >= errores_max and gap > 0:
        resultado = "frustracion"
    elif gap <= tolerancia:
        resultado = "correcto"
    elif gap >= umbral_frus:
        resultado = "frustracion"
    elif gap >= umbral_error:
        resultado = "error_conceptual"
    else:
        # Zona borderline: pequeño ruido determinista por seed → mezcla correcto / error
        resultado = "correcto" if rng.random() > 0.5 else "error_conceptual"

    respuesta_correcta = str(item.get("respuesta_correcta", ""))
    if resultado == "correcto":
        respuesta_sim = respuesta_correcta
    elif resultado == "error_conceptual":
        respuesta_sim = f"(respuesta confusa — {item.get('concepto', '')})"
    else:
        respuesta_sim = "(en blanco — abandona el ítem)"

    return {
        "item_id": item.get("id"),
        "concepto": item.get("concepto"),
        "dificultad_item": dificultad,
        "habilidad_pre": round(habilidad, 2),
        "gap": round(gap, 2),
        "resultado": resultado,
        "respuesta_sim": respuesta_sim,
        "respuesta_correcta": respuesta_correcta,
        "retroalimentacion": item.get("retroalimentacion", ""),
        "ts": _now_iso(),
    }


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def cargar_perfil(state: TutorState) -> dict:
    """Carga estudiante, política y banco de ítems del dominio."""
    student_id = state.get("student_id", "STU-001")
    data = get_data_dir()
    student = get_student(student_id, data)
    policy = get_policy(data)
    item_bank = get_item_bank(data)

    dominio = student.get("dominio", "")
    # El banco completo pertenece al dominio "fracciones_porcentajes" en DEMO;
    # un dominio distinto del estudiante igual recibe todos los ítems disponibles.
    items = sorted(list(item_bank), key=lambda x: float(x.get("dificultad", 5.0)))

    habilidad_inicial = student.get("habilidad_inicial")
    diagnostico_aplicado = habilidad_inicial is not None
    if habilidad_inicial is None:
        habilidad_inicial = float(policy.get("habilidad_inicial_default", 4.0))
    habilidad_inicial = float(habilidad_inicial)

    max_items = int(policy.get("max_items_sesion", 6))

    logger.info(
        "Perfil cargado: student=%s diagnostico_previo=%s habilidad_inicial=%.2f items_dominio=%d",
        student_id, diagnostico_aplicado, habilidad_inicial, len(items),
    )

    return {
        "student": student,
        "policy": policy,
        "items_disponibles": items,
        "items_servidos": [],
        "habilidad": habilidad_inicial,
        "habilidad_inicial": habilidad_inicial,
        "diagnostico_aplicado": diagnostico_aplicado,
        "max_items": max_items,
        "evaluaciones": [],
        "conceptos_dominados": [],
        "conceptos_a_remediar": [],
        "errores_consecutivos": 0,
        "ajuste_ultimo": "",
        "current_item": {},
        "evaluacion_actual": {},
        "events": [{
            "type": "perfil_cargado",
            "student_id": student_id,
            "nombre": student.get("nombre"),
            "curso": student.get("curso"),
            "dominio": dominio,
            "diagnostico_previo": diagnostico_aplicado,
            "habilidad_inicial": round(habilidad_inicial, 2),
            "items_disponibles": len(items),
        }],
    }


# ---------------------------------------------------------------------------
# Router 1: necesidad de diagnóstico
# ---------------------------------------------------------------------------

def diagnostico_router(state: TutorState) -> str:
    return "con_diagnostico" if state.get("diagnostico_aplicado", False) else "sin_diagnostico"


def aplicar_diagnostico(state: TutorState) -> dict:
    """
    Pretest determinista: aplica `diagnostico_items` ítems repartidos en el rango de
    dificultad y fija la habilidad inicial al último nivel donde el simulador acierta.
    """
    policy = state.get("policy", {})
    items_all = state.get("items_disponibles", [])
    student = state.get("student", {})
    rng = random.Random(int(student.get("seed", 0)))

    n = int(policy.get("diagnostico_items", 3))
    if not items_all or n <= 0:
        return {
            "diagnostico_aplicado": True,
            "events": [{"type": "diagnostico_omitido", "razon": "sin banco de ítems"}],
        }

    # Selecciona n ítems repartidos uniformemente por percentiles del banco.
    paso = max(1, len(items_all) // (n + 1))
    seleccion = [items_all[min((i + 1) * paso, len(items_all) - 1)] for i in range(n)]

    habilidad = state.get("habilidad", float(policy.get("habilidad_inicial_default", 4.0)))
    detalle: list = []
    for it in seleccion:
        ev = _simulate_response(it, habilidad, policy, 0, rng)
        detalle.append(ev)
        if ev["resultado"] == "correcto":
            habilidad = _clamp(habilidad + 0.5, policy.get("habilidad_min", 1.0), policy.get("habilidad_max", 10.0))
        elif ev["resultado"] == "frustracion":
            habilidad = _clamp(habilidad - 0.8, policy.get("habilidad_min", 1.0), policy.get("habilidad_max", 10.0))

    logger.info(
        "Diagnóstico aplicado: %d ítems, habilidad_estimada=%.2f",
        len(detalle), habilidad,
    )

    return {
        "habilidad": habilidad,
        "habilidad_inicial": habilidad,
        "diagnostico_aplicado": True,
        "events": [{
            "type": "diagnostico_aplicado",
            "items": [d["item_id"] for d in detalle],
            "resultados": [d["resultado"] for d in detalle],
            "habilidad_estimada": round(habilidad, 2),
        }],
    }


# ---------------------------------------------------------------------------
# Bucle adaptativo
# ---------------------------------------------------------------------------

def seleccionar_item(state: TutorState) -> dict:
    """
    Elige el ítem con dificultad más cercana a la habilidad actual,
    que aún no haya sido servido. Prefiere formato del estudiante en empates.
    """
    habilidad = float(state.get("habilidad", 4.0))
    servidos = set(state.get("items_servidos", []))
    items = state.get("items_disponibles", [])
    student = state.get("student", {})
    formato_pref = student.get("preferencia_formato", "")

    candidatos = [it for it in items if it.get("id") not in servidos]
    if not candidatos:
        return {
            "current_item": {},
            "events": [{"type": "sin_items_disponibles"}],
        }

    def _score(it: dict) -> tuple:
        gap = abs(float(it.get("dificultad", 5.0)) - habilidad)
        empate = 0 if it.get("formato") == formato_pref else 1
        return (gap, empate)

    elegido = min(candidatos, key=_score)
    nuevos_servidos = state.get("items_servidos", []) + [elegido.get("id")]

    logger.info(
        "Ítem seleccionado: id=%s concepto=%s dificultad=%.2f (habilidad=%.2f)",
        elegido.get("id"), elegido.get("concepto"),
        float(elegido.get("dificultad", 0)), habilidad,
    )

    return {
        "current_item": elegido,
        "items_servidos": nuevos_servidos,
        "events": [{
            "type": "item_seleccionado",
            "item_id": elegido.get("id"),
            "concepto": elegido.get("concepto"),
            "dificultad": float(elegido.get("dificultad", 0)),
            "formato": elegido.get("formato"),
            "indice": len(nuevos_servidos),
        }],
    }


def presentar_actividad(state: TutorState) -> dict:
    """Emite el ítem hacia la UI (en una integración real, lo entregaría al frontend)."""
    item = state.get("current_item", {})
    if not item:
        return {"events": [{"type": "presentacion_omitida"}]}

    return {
        "events": [{
            "type": "actividad_presentada",
            "item_id": item.get("id"),
            "prompt": item.get("prompt", ""),
            "formato": item.get("formato"),
        }],
    }


def evaluar_respuesta(state: TutorState) -> dict:
    """Simulador determinista (per-student seed) de la respuesta del estudiante."""
    item = state.get("current_item", {})
    if not item:
        return {"events": [{"type": "evaluacion_omitida"}]}

    policy = state.get("policy", {})
    student = state.get("student", {})
    rng = random.Random(
        int(student.get("seed", 0)) + len(state.get("evaluaciones", [])) * 7919
    )

    ev = _simulate_response(
        item,
        float(state.get("habilidad", 4.0)),
        policy,
        int(state.get("errores_consecutivos", 0)),
        rng,
    )

    evals = state.get("evaluaciones", []) + [ev]

    logger.info(
        "Evaluación: item=%s resultado=%s gap=%.2f",
        ev["item_id"], ev["resultado"], ev["gap"],
    )

    return {
        "evaluacion_actual": ev,
        "evaluaciones": evals,
        "events": [{
            "type": "respuesta_evaluada",
            "item_id": ev["item_id"],
            "resultado": ev["resultado"],
            "gap": ev["gap"],
            "habilidad_pre": ev["habilidad_pre"],
        }],
    }


# ---------------------------------------------------------------------------
# Router 2: desempeño
# ---------------------------------------------------------------------------

def desempeno_router(state: TutorState) -> str:
    ev = state.get("evaluacion_actual", {})
    res = ev.get("resultado", "correcto")
    if res == "correcto":
        return "domina"
    if res == "frustracion":
        return "frustracion"
    return "error_conceptual"


def aumentar_dificultad(state: TutorState) -> dict:
    policy = state.get("policy", {})
    delta = float(policy.get("delta_aumento", 0.7))
    nueva = _clamp(
        float(state.get("habilidad", 4.0)) + delta,
        float(policy.get("habilidad_min", 1.0)),
        float(policy.get("habilidad_max", 10.0)),
    )
    ev = state.get("evaluacion_actual", {})
    concepto = ev.get("concepto")
    dominados = state.get("conceptos_dominados", [])
    if concepto and concepto not in dominados:
        dominados = dominados + [concepto]

    return {
        "habilidad": nueva,
        "errores_consecutivos": 0,
        "conceptos_dominados": dominados,
        "ajuste_ultimo": "aumentar",
        "events": [{
            "type": "dificultad_aumentada",
            "habilidad": round(nueva, 2),
            "concepto_dominado": concepto,
        }],
    }


def remediar_concepto(state: TutorState) -> dict:
    policy = state.get("policy", {})
    delta = float(policy.get("delta_remediar", -0.3))
    nueva = _clamp(
        float(state.get("habilidad", 4.0)) + delta,
        float(policy.get("habilidad_min", 1.0)),
        float(policy.get("habilidad_max", 10.0)),
    )
    ev = state.get("evaluacion_actual", {})
    concepto = ev.get("concepto")
    pendientes = state.get("conceptos_a_remediar", [])
    if concepto and concepto not in pendientes:
        pendientes = pendientes + [concepto]

    return {
        "habilidad": nueva,
        "errores_consecutivos": int(state.get("errores_consecutivos", 0)) + 1,
        "conceptos_a_remediar": pendientes,
        "ajuste_ultimo": "remediar",
        "events": [{
            "type": "concepto_remediado",
            "habilidad": round(nueva, 2),
            "concepto": concepto,
            "retroalimentacion": ev.get("retroalimentacion", ""),
        }],
    }


def reducir_dificultad(state: TutorState) -> dict:
    policy = state.get("policy", {})
    delta = float(policy.get("delta_reducir", -0.6))
    nueva = _clamp(
        float(state.get("habilidad", 4.0)) + delta,
        float(policy.get("habilidad_min", 1.0)),
        float(policy.get("habilidad_max", 10.0)),
    )

    return {
        "habilidad": nueva,
        "errores_consecutivos": 0,
        "ajuste_ultimo": "reducir",
        "events": [{
            "type": "dificultad_reducida",
            "habilidad": round(nueva, 2),
            "razon": "frustracion o racha de errores",
        }],
    }


# ---------------------------------------------------------------------------
# Router 3: continuar / finalizar
# ---------------------------------------------------------------------------

def continuar_router(state: TutorState) -> str:
    servidos = len(state.get("items_servidos", []))
    max_items = int(state.get("max_items", 6))
    quedan = len(state.get("items_disponibles", [])) - servidos
    if servidos >= max_items or quedan <= 0:
        return "finalizar"
    return "continuar"


def actualizar_perfil(state: TutorState) -> dict:
    """Calcula métricas finales y recomendación para próxima sesión."""
    evals = state.get("evaluaciones", [])
    total = len(evals)
    aciertos = sum(1 for e in evals if e.get("resultado") == "correcto")
    errores_conc = sum(1 for e in evals if e.get("resultado") == "error_conceptual")
    frus = sum(1 for e in evals if e.get("resultado") == "frustracion")
    tasa_acierto = round(aciertos / total, 2) if total else 0.0

    policy = state.get("policy", {})
    promocion = tasa_acierto >= float(policy.get("min_aciertos_promocion", 0.6))

    habilidad_inicial = float(state.get("habilidad_inicial", 4.0))
    habilidad_final = float(state.get("habilidad", habilidad_inicial))
    delta = round(habilidad_final - habilidad_inicial, 2)

    if promocion and not state.get("conceptos_a_remediar"):
        recomendacion = "Avanzar al siguiente bloque temático en próxima sesión."
    elif state.get("conceptos_a_remediar"):
        recomendacion = (
            "Iniciar próxima sesión con remediación de: "
            + ", ".join(state.get("conceptos_a_remediar", []))
        )
    else:
        recomendacion = "Consolidar nivel actual con práctica adicional en el mismo rango."

    perfil = {
        "student_id": state.get("student_id"),
        "nombre": state.get("student", {}).get("nombre"),
        "items_resueltos": total,
        "aciertos": aciertos,
        "errores_conceptuales": errores_conc,
        "frustraciones": frus,
        "tasa_acierto": tasa_acierto,
        "habilidad_inicial": round(habilidad_inicial, 2),
        "habilidad_final": round(habilidad_final, 2),
        "delta_habilidad": delta,
        "conceptos_dominados": state.get("conceptos_dominados", []),
        "conceptos_a_remediar": state.get("conceptos_a_remediar", []),
        "promocion": promocion,
        "recomendacion_proxima": recomendacion,
        "fecha": _now_iso(),
    }

    logger.info(
        "Perfil actualizado: tasa=%.2f delta_habilidad=%+.2f promocion=%s",
        tasa_acierto, delta, promocion,
    )

    return {
        "perfil_final": perfil,
        "events": [{
            "type": "perfil_actualizado",
            "tasa_acierto": tasa_acierto,
            "habilidad_final": perfil["habilidad_final"],
            "delta_habilidad": delta,
            "promocion": promocion,
        }],
    }


def producir_reporte(state: TutorState) -> dict:
    """Reporte ejecutivo para docente / institución (Markdown, LLM opt-in)."""
    perfil = state.get("perfil_final", {})
    student = state.get("student", {})
    evals = state.get("evaluaciones", [])

    estado_icon = "🟢" if perfil.get("promocion") else "🟡"
    line_eval = "\n".join(
        f"  - {e.get('item_id')} ({e.get('concepto')}) "
        f"dif={e.get('dificultad_item')} → {e.get('resultado')}"
        for e in evals
    )

    fallback = (
        f"## Reporte de tutoría — {student.get('nombre', '')} ({state.get('student_id', '')})\n\n"
        f"**Curso:** {student.get('curso', '—')} · "
        f"**Dominio:** {student.get('dominio', '—')} · "
        f"**Objetivo:** {student.get('objetivo_sesion', '—')}\n\n"
        f"### Resumen de la sesión {estado_icon}\n"
        f"- Ítems resueltos: **{perfil.get('items_resueltos', 0)}** "
        f"({perfil.get('aciertos', 0)} aciertos / "
        f"{perfil.get('errores_conceptuales', 0)} errores conceptuales / "
        f"{perfil.get('frustraciones', 0)} frustración)\n"
        f"- Tasa de acierto: **{perfil.get('tasa_acierto', 0) * 100:.0f}%**\n"
        f"- Habilidad: {perfil.get('habilidad_inicial', 0)} → "
        f"**{perfil.get('habilidad_final', 0)}** "
        f"({perfil.get('delta_habilidad', 0):+.2f})\n"
        f"- Promoción: {'sí' if perfil.get('promocion') else 'no'}\n\n"
        f"### Conceptos\n"
        f"- Dominados: {', '.join(perfil.get('conceptos_dominados', [])) or '—'}\n"
        f"- A remediar: {', '.join(perfil.get('conceptos_a_remediar', [])) or '—'}\n\n"
        f"### Ítems aplicados\n{line_eval or '  - (sin ítems)'}\n\n"
        f"### Recomendación para la próxima sesión\n"
        f"{perfil.get('recomendacion_proxima', '—')}\n\n"
        f"_Reporte generado por el agente tutor — Caso 11. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres un docente jefe que redacta un reporte de tutoría en español "
            f"(máx 220 palabras) para el apoderado y el coordinador. "
            f"Estudiante: {student.get('nombre')} ({student.get('curso')}). "
            f"Dominio: {student.get('dominio')}. "
            f"Sesión: {perfil.get('items_resueltos')} ítems, "
            f"tasa de acierto {perfil.get('tasa_acierto') * 100:.0f}%. "
            f"Habilidad {perfil.get('habilidad_inicial')} → {perfil.get('habilidad_final')} "
            f"(Δ {perfil.get('delta_habilidad'):+.2f}). "
            f"Conceptos dominados: {perfil.get('conceptos_dominados')}. "
            f"A remediar: {perfil.get('conceptos_a_remediar')}. "
            f"Cierra con 2 acciones concretas para la próxima sesión."
        )
        reporte = _llm_invoke(prompt, fallback)
    else:
        reporte = fallback

    logger.info(
        "Reporte generado: student=%s items=%d modo=%s",
        state.get("student_id"), perfil.get("items_resueltos", 0),
        "LIVE" if _LIVE_MODE else "DEMO",
    )

    return {
        "reporte": reporte,
        "done": True,
        "events": [{
            "type": "sesion_completada",
            "student_id": state.get("student_id"),
            "items": perfil.get("items_resueltos", 0),
            "tasa_acierto": perfil.get("tasa_acierto", 0.0),
            "promocion": bool(perfil.get("promocion", False)),
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(TutorState)

    builder.add_node("cargar_perfil", cargar_perfil)
    builder.add_node("aplicar_diagnostico", aplicar_diagnostico)
    builder.add_node("seleccionar_item", seleccionar_item)
    builder.add_node("presentar_actividad", presentar_actividad)
    builder.add_node("evaluar_respuesta", evaluar_respuesta)
    builder.add_node("aumentar_dificultad", aumentar_dificultad)
    builder.add_node("remediar_concepto", remediar_concepto)
    builder.add_node("reducir_dificultad", reducir_dificultad)
    builder.add_node("actualizar_perfil", actualizar_perfil)
    builder.add_node("producir_reporte", producir_reporte)

    builder.set_entry_point("cargar_perfil")

    builder.add_conditional_edges(
        "cargar_perfil",
        diagnostico_router,
        {
            "sin_diagnostico": "aplicar_diagnostico",
            "con_diagnostico": "seleccionar_item",
        },
    )
    builder.add_edge("aplicar_diagnostico", "seleccionar_item")
    builder.add_edge("seleccionar_item", "presentar_actividad")
    builder.add_edge("presentar_actividad", "evaluar_respuesta")

    builder.add_conditional_edges(
        "evaluar_respuesta",
        desempeno_router,
        {
            "domina": "aumentar_dificultad",
            "error_conceptual": "remediar_concepto",
            "frustracion": "reducir_dificultad",
        },
    )

    builder.add_conditional_edges(
        "aumentar_dificultad",
        continuar_router,
        {"continuar": "seleccionar_item", "finalizar": "actualizar_perfil"},
    )
    builder.add_conditional_edges(
        "remediar_concepto",
        continuar_router,
        {"continuar": "seleccionar_item", "finalizar": "actualizar_perfil"},
    )
    builder.add_conditional_edges(
        "reducir_dificultad",
        continuar_router,
        {"continuar": "seleccionar_item", "finalizar": "actualizar_perfil"},
    )

    builder.add_edge("actualizar_perfil", "producir_reporte")
    builder.add_edge("producir_reporte", END)

    return builder.compile(checkpointer=MemorySaver())
