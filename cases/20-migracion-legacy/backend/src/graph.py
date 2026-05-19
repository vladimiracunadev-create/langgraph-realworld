"""
graph.py — Grafo LangGraph para el Caso 20: Migración de Sistemas Legacy.

Pipeline con 2 routers + loops de regresión y de avance de lotes:

  analizar_codigo_legacy → mapear_dependencias → planificar_migracion
       → seleccionar_lote → refactorizar_modulo → generar_tests_equivalencia
       → ejecutar_tests
            → resultado_tests_router
                  ├─ ok            → registrar_progreso
                  ├─ falla∧iter<max → analizar_regresion → refactorizar_modulo
                  └─ falla∧tope    → registrar_progreso (workaround)
       → migracion_completa_router
            ├─ pendientes → seleccionar_lote
            └─ vacío      → validacion_integral → END

DEMO: ejecución simulada determinista (sin red ni LLM real).
LIVE opt-in con OPENAI_API_KEY sólo para el resumen ejecutivo final.
"""
from __future__ import annotations

import logging
import operator
import os
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import (
    get_dependencias,
    get_lotes_catalog,
    get_policy,
    get_proyecto,
)
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class MigracionState(TypedDict):
    proyecto_id: str
    proyecto: dict
    dependencias: dict
    plan_migracion: list
    lote_actual: str
    lotes_completados: list
    lotes_pendientes: list
    codigo_refactorizado: dict
    tests_generados: dict
    resultado_tests: dict
    iter_regresion: dict
    progreso: list
    regresiones: list
    reporte_final: str
    estado_final: str
    metricas: dict
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


def _orden_topologico(modulos: list, deps: dict) -> list:
    """Kahn's algorithm. Ante empate, ordena por riesgo descendente (resuelto luego)."""
    pendientes = list(modulos)
    resultado: list = []
    visitados: set = set()
    while pendientes:
        # encontrar nodos cuyas dependencias ya estén resueltas
        disponibles = [m for m in pendientes
                       if all(d in visitados for d in deps.get(m, []))]
        if not disponibles:
            # ciclo o dependencia externa: añadir lo que queda y salir
            resultado.extend(pendientes)
            break
        # estabilidad: orden por nombre
        disponibles.sort()
        siguiente = disponibles[0]
        resultado.append(siguiente)
        visitados.add(siguiente)
        pendientes.remove(siguiente)
    return resultado


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def analizar_codigo_legacy(state: MigracionState) -> dict:
    pid = state.get("proyecto_id", "P-001")
    proyecto = get_proyecto(pid, get_data_dir())

    logger.info(
        "Código legacy analizado: id=%s origen=%s destino=%s loc=%d",
        pid, proyecto.get("lenguaje_origen"),
        proyecto.get("lenguaje_destino"), proyecto.get("loc_total", 0),
    )

    return {
        "proyecto": proyecto,
        "codigo_refactorizado": {},
        "tests_generados": {},
        "resultado_tests": {},
        "iter_regresion": {},
        "progreso": [],
        "regresiones": [],
        "lotes_completados": [],
        "events": [{
            "type": "codigo_analizado",
            "proyecto_id": pid,
            "lenguaje_origen": proyecto.get("lenguaje_origen"),
            "lenguaje_destino": proyecto.get("lenguaje_destino"),
            "modulos": proyecto.get("modulos", []),
            "loc_total": proyecto.get("loc_total", 0),
        }],
    }


def mapear_dependencias(state: MigracionState) -> dict:
    pid = state.get("proyecto_id", "P-001")
    deps = get_dependencias(pid, get_data_dir())
    logger.info("Dependencias mapeadas: %d módulos.", len(deps))
    return {
        "dependencias": deps,
        "events": [{
            "type": "dependencias_mapeadas",
            "proyecto_id": pid,
            "nodos": len(deps),
            "aristas": sum(len(v) for v in deps.values()),
        }],
    }


def planificar_migracion(state: MigracionState) -> dict:
    pid = state.get("proyecto_id", "P-001")
    proyecto = state.get("proyecto", {})
    deps = state.get("dependencias", {})
    catalog = get_lotes_catalog(pid, get_data_dir())

    modulos = proyecto.get("modulos", []) or list(deps.keys())
    orden = _orden_topologico(modulos, deps)

    plan = []
    for m in orden:
        cfg = catalog.get(m, {})
        plan.append({
            "modulo": m,
            "complejidad": cfg.get("complejidad", 0),
            "riesgo": cfg.get("riesgo", 0),
            "loc": cfg.get("loc", 0),
            "no_migrable": bool(cfg.get("no_migrable", False)),
        })

    logger.info("Plan de migración generado: %d lotes.", len(plan))

    return {
        "plan_migracion": plan,
        "lotes_pendientes": [p["modulo"] for p in plan],
        "events": [{
            "type": "plan_generado",
            "proyecto_id": pid,
            "lotes": [p["modulo"] for p in plan],
            "total_lotes": len(plan),
        }],
    }


def seleccionar_lote(state: MigracionState) -> dict:
    pendientes = state.get("lotes_pendientes", [])
    if not pendientes:
        return {
            "lote_actual": "",
            "events": [{"type": "sin_lotes_pendientes"}],
        }
    siguiente = pendientes[0]
    iter_reg = dict(state.get("iter_regresion", {}))
    if siguiente not in iter_reg:
        iter_reg[siguiente] = 0

    logger.info("Lote seleccionado: %s", siguiente)

    return {
        "lote_actual": siguiente,
        "iter_regresion": iter_reg,
        "events": [{
            "type": "lote_seleccionado",
            "modulo": siguiente,
            "restantes": len(pendientes),
        }],
    }


def refactorizar_modulo(state: MigracionState) -> dict:
    pid = state.get("proyecto_id", "P-001")
    catalog = get_lotes_catalog(pid, get_data_dir())
    modulo = state.get("lote_actual", "")
    cfg = catalog.get(modulo, {})

    refactor = dict(state.get("codigo_refactorizado", {}))
    refactor[modulo] = {
        "codigo_origen": cfg.get("codigo_origen", ""),
        "codigo_destino": cfg.get("codigo_destino", ""),
        "loc": cfg.get("loc", 0),
        "complejidad": cfg.get("complejidad", 0),
    }

    logger.info("Módulo refactorizado: %s (loc=%d)", modulo, cfg.get("loc", 0))

    return {
        "codigo_refactorizado": refactor,
        "events": [{
            "type": "modulo_refactorizado",
            "modulo": modulo,
            "loc": cfg.get("loc", 0),
            "complejidad": cfg.get("complejidad", 0),
        }],
    }


def generar_tests_equivalencia(state: MigracionState) -> dict:
    pid = state.get("proyecto_id", "P-001")
    catalog = get_lotes_catalog(pid, get_data_dir())
    modulo = state.get("lote_actual", "")
    cfg = catalog.get(modulo, {})

    tests = dict(state.get("tests_generados", {}))
    tests[modulo] = list(cfg.get("tests_esperados", []))

    logger.info("Tests de equivalencia generados: modulo=%s n=%d",
                modulo, len(tests[modulo]))

    return {
        "tests_generados": tests,
        "events": [{
            "type": "tests_generados",
            "modulo": modulo,
            "n_tests": len(tests[modulo]),
        }],
    }


def ejecutar_tests(state: MigracionState) -> dict:
    pid = state.get("proyecto_id", "P-001")
    catalog = get_lotes_catalog(pid, get_data_dir())
    modulo = state.get("lote_actual", "")
    cfg = catalog.get(modulo, {})
    policy = get_policy(get_data_dir())
    max_reg = policy.get("max_regresiones_por_lote", 2)

    iter_reg = state.get("iter_regresion", {}).get(modulo, 0)
    falla = bool(cfg.get("falla_simulada", False))

    # Si el módulo es no_migrable, siempre falla
    if cfg.get("no_migrable", False):
        ok = False
        detalle = "modulo_no_migrable"
    elif falla and cfg.get("regresion_simulada", False) and iter_reg >= 1:
        # primera regresión arregla el problema
        ok = True
        detalle = "fix_post_regresion"
    elif falla and not cfg.get("regresion_simulada", False):
        # falla persistente -> agotará iteraciones
        ok = False
        detalle = "falla_persistente"
    elif falla:
        ok = False
        detalle = "falla_inicial"
    else:
        ok = True
        detalle = "pass_directo"

    tests = state.get("tests_generados", {}).get(modulo, [])
    resultados = {
        "ok": ok,
        "modulo": modulo,
        "n_tests": len(tests),
        "detalle": detalle,
        "iter_regresion": iter_reg,
        "max_regresiones": max_reg,
    }

    nuevo_resultado = dict(state.get("resultado_tests", {}))
    nuevo_resultado[modulo] = resultados

    logger.info(
        "Tests ejecutados: modulo=%s ok=%s iter_reg=%d/%d detalle=%s",
        modulo, ok, iter_reg, max_reg, detalle,
    )

    return {
        "resultado_tests": nuevo_resultado,
        "events": [{
            "type": "tests_ejecutados",
            "modulo": modulo,
            "ok": ok,
            "n_tests": len(tests),
            "detalle": detalle,
            "iter_regresion": iter_reg,
        }],
    }


def resultado_tests_router(
    state: MigracionState,
) -> Literal["analizar_regresion", "registrar_progreso"]:
    modulo = state.get("lote_actual", "")
    resultado = state.get("resultado_tests", {}).get(modulo, {})
    if resultado.get("ok"):
        return "registrar_progreso"
    iter_reg = state.get("iter_regresion", {}).get(modulo, 0)
    policy = get_policy(get_data_dir())
    max_reg = policy.get("max_regresiones_por_lote", 2)
    if iter_reg < max_reg:
        return "analizar_regresion"
    return "registrar_progreso"


def analizar_regresion(state: MigracionState) -> dict:
    pid = state.get("proyecto_id", "P-001")
    catalog = get_lotes_catalog(pid, get_data_dir())
    modulo = state.get("lote_actual", "")
    cfg = catalog.get(modulo, {})

    iter_reg_map = dict(state.get("iter_regresion", {}))
    iter_reg_map[modulo] = iter_reg_map.get(modulo, 0) + 1
    nueva_iter = iter_reg_map[modulo]

    regresiones = list(state.get("regresiones", []))
    fix_simulado = (
        f"Aplicar fix de tipos/encoding en {modulo} (iter {nueva_iter}): "
        f"normalizar entrada y reintentar refactor."
    )
    regresiones.append({
        "modulo": modulo,
        "iter": nueva_iter,
        "fix": fix_simulado,
        "complejidad_original": cfg.get("complejidad", 0),
    })

    logger.info(
        "Regresión analizada: modulo=%s iter=%d",
        modulo, nueva_iter,
    )

    return {
        "iter_regresion": iter_reg_map,
        "regresiones": regresiones,
        "events": [{
            "type": "regresion_analizada",
            "modulo": modulo,
            "iter": nueva_iter,
            "fix": fix_simulado,
        }],
    }


def registrar_progreso(state: MigracionState) -> dict:
    modulo = state.get("lote_actual", "")
    resultado = state.get("resultado_tests", {}).get(modulo, {})
    pendientes = [m for m in state.get("lotes_pendientes", []) if m != modulo]
    completados = list(state.get("lotes_completados", []))

    estado_lote = "ok" if resultado.get("ok") else "fallido_con_workaround"
    progreso = list(state.get("progreso", []))
    progreso.append({
        "modulo": modulo,
        "estado": estado_lote,
        "iter_regresion": state.get("iter_regresion", {}).get(modulo, 0),
        "n_tests": resultado.get("n_tests", 0),
        "detalle": resultado.get("detalle", ""),
    })
    completados.append({"modulo": modulo, "estado": estado_lote})

    logger.info(
        "Progreso registrado: modulo=%s estado=%s pendientes=%d",
        modulo, estado_lote, len(pendientes),
    )

    return {
        "progreso": progreso,
        "lotes_completados": completados,
        "lotes_pendientes": pendientes,
        "events": [{
            "type": "progreso_registrado",
            "modulo": modulo,
            "estado": estado_lote,
            "pendientes": len(pendientes),
        }],
    }


def migracion_completa_router(
    state: MigracionState,
) -> Literal["seleccionar_lote", "validacion_integral"]:
    if state.get("lotes_pendientes", []):
        return "seleccionar_lote"
    return "validacion_integral"


def validacion_integral(state: MigracionState) -> dict:
    completados = state.get("lotes_completados", [])
    workarounds = [c for c in completados if c.get("estado") == "fallido_con_workaround"]
    ok_count = len(completados) - len(workarounds)

    if not completados:
        estado_final = "sin_lotes"
    elif workarounds:
        estado_final = "parcial"
    else:
        estado_final = "exitosa"

    proyecto = state.get("proyecto", {})
    metricas = {
        "estado_final": estado_final,
        "lotes_totales": len(completados),
        "lotes_ok": ok_count,
        "lotes_workaround": len(workarounds),
        "regresiones_totales": len(state.get("regresiones", [])),
        "lenguaje_origen": proyecto.get("lenguaje_origen"),
        "lenguaje_destino": proyecto.get("lenguaje_destino"),
        "loc_total": proyecto.get("loc_total", 0),
    }

    progreso = state.get("progreso", [])
    detalle_md = "\n".join(
        f"- **{p['modulo']}** — estado: `{p['estado']}`, "
        f"iter_regresion: {p['iter_regresion']}, n_tests: {p['n_tests']}, "
        f"detalle: {p['detalle']}"
        for p in progreso
    )

    fallback = (
        f"## Reporte de Migración — {proyecto.get('nombre','?')} ({proyecto.get('id','?')})\n\n"
        f"**Origen → Destino:** {proyecto.get('lenguaje_origen','?')} → "
        f"{proyecto.get('lenguaje_destino','?')}\n"
        f"**Estado final:** `{estado_final}`\n"
        f"**Lotes totales:** {metricas['lotes_totales']} — OK: {ok_count} — "
        f"Workaround: {len(workarounds)}\n"
        f"**Regresiones aplicadas:** {metricas['regresiones_totales']}\n\n"
        f"### Detalle por lote\n{detalle_md}\n\n"
        f"_Generado por agente de migración · Caso 20. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres líder técnico de migración. Redacta en español (máx 150 palabras) "
            f"un reporte ejecutivo del proyecto {proyecto.get('id')} "
            f"({proyecto.get('lenguaje_origen')} → {proyecto.get('lenguaje_destino')}) "
            f"con estado final '{estado_final}', {len(completados)} lotes, "
            f"{len(workarounds)} workarounds y "
            f"{metricas['regresiones_totales']} regresiones."
        )
        reporte = _llm_invoke(prompt, fallback)
    else:
        reporte = fallback

    logger.info(
        "Validación integral: estado=%s lotes=%d workarounds=%d",
        estado_final, len(completados), len(workarounds),
    )

    return {
        "reporte_final": reporte,
        "estado_final": estado_final,
        "metricas": metricas,
        "done": True,
        "events": [{
            "type": "migracion_completada",
            "proyecto_id": proyecto.get("id"),
            "estado_final": estado_final,
            "lotes_totales": len(completados),
            "workarounds": len(workarounds),
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(MigracionState)

    builder.add_node("analizar_codigo_legacy", analizar_codigo_legacy)
    builder.add_node("mapear_dependencias", mapear_dependencias)
    builder.add_node("planificar_migracion", planificar_migracion)
    builder.add_node("seleccionar_lote", seleccionar_lote)
    builder.add_node("refactorizar_modulo", refactorizar_modulo)
    builder.add_node("generar_tests_equivalencia", generar_tests_equivalencia)
    builder.add_node("ejecutar_tests", ejecutar_tests)
    builder.add_node("analizar_regresion", analizar_regresion)
    builder.add_node("registrar_progreso", registrar_progreso)
    builder.add_node("validacion_integral", validacion_integral)

    builder.set_entry_point("analizar_codigo_legacy")
    builder.add_edge("analizar_codigo_legacy", "mapear_dependencias")
    builder.add_edge("mapear_dependencias", "planificar_migracion")
    builder.add_edge("planificar_migracion", "seleccionar_lote")
    builder.add_edge("seleccionar_lote", "refactorizar_modulo")
    builder.add_edge("refactorizar_modulo", "generar_tests_equivalencia")
    builder.add_edge("generar_tests_equivalencia", "ejecutar_tests")

    builder.add_conditional_edges(
        "ejecutar_tests",
        resultado_tests_router,
        {
            "analizar_regresion": "analizar_regresion",
            "registrar_progreso": "registrar_progreso",
        },
    )
    builder.add_edge("analizar_regresion", "refactorizar_modulo")

    builder.add_conditional_edges(
        "registrar_progreso",
        migracion_completa_router,
        {
            "seleccionar_lote": "seleccionar_lote",
            "validacion_integral": "validacion_integral",
        },
    )

    builder.add_edge("validacion_integral", END)

    return builder.compile(checkpointer=MemorySaver())
