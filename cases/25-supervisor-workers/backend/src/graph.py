"""
graph.py — Grafo Supervisor-Workers para Due Diligence (Caso 25).

Patrón: Supervisor orquesta workers secuenciales especializados.
Cada worker ejecuta un análisis independiente (financiero, legal,
operacional, reputacional) y el supervisor consolida los resultados.

Nota: Se usa flujo secuencial robusto en lugar de Send API para
garantizar compatibilidad con todas las versiones de LangGraph >= 0.2.
"""
from __future__ import annotations

import logging
import operator
import time
from typing import Annotated, Any, Dict, List

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from .settings import data_dir, load_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Estado del Supervisor
# ---------------------------------------------------------------------------

class SupervisorState(TypedDict, total=False):
    """Estado centralizado del orquestador supervisor."""
    task_id: str
    task: Dict[str, Any]
    subtasks: List[str]           # tipos de worker a ejecutar
    worker_results: Annotated[List[Dict[str, Any]], operator.add]  # acumula resultados
    conflicts: List[str]
    final_report: str
    events: Annotated[List[Dict[str, Any]], operator.add]
    done: bool


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _now_ms() -> int:
    return int(time.time() * 1000)


def _push_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "events": [
            {
                "ts": _now_ms(),
                "type": event_type,
                "data": data,
            }
        ]
    }


def _run_worker_analysis(task: Dict[str, Any], worker_type: str) -> Dict[str, Any]:
    """Ejecuta el análisis correspondiente al tipo de worker."""
    from .integrations import (
        financial_analysis_stub,
        legal_analysis_stub,
        operational_analysis_stub,
        reputational_analysis_stub,
    )

    company = task.get("company", "Empresa Desconocida")
    budget = float(task.get("budget_usd", 0))

    dispatch = {
        "financial": lambda: financial_analysis_stub(company, budget),
        "legal": lambda: legal_analysis_stub(company),
        "operational": lambda: operational_analysis_stub(company),
        "reputational": lambda: reputational_analysis_stub(company),
    }

    fn = dispatch.get(worker_type)
    if fn is None:
        return {"error": f"worker_type desconocido: {worker_type}"}

    return fn()


# ---------------------------------------------------------------------------
# Nodos del Supervisor
# ---------------------------------------------------------------------------

def load_task(state: SupervisorState) -> SupervisorState:
    """Nodo inicial: carga la tarea de due diligence desde el archivo de datos."""
    load_settings()
    task_id = state.get("task_id", "DDL-2026-001")
    logger.info(f"Cargando tarea: {task_id}")

    from .integrations import get_task
    task = get_task(task_id, data_dir())

    out: SupervisorState = {
        "task_id": task_id,
        "task": task,
        "subtasks": [],
        "worker_results": [],
        "conflicts": [],
        "final_report": "",
        "done": False,
        "events": state.get("events", []) or [],
    }
    out.update(
        _push_event("task_loaded", {
            "task_id": task_id,
            "company": task.get("company"),
            "budget_usd": task.get("budget_usd"),
        })
    )
    return out


def decompose_task(state: SupervisorState) -> SupervisorState:
    """
    Nodo de descomposición: el supervisor determina qué workers ejecutar
    basándose en la tarea y su prioridad.
    """
    task = state.get("task", {})
    priority = task.get("priority", "normal")
    logger.info(f"Descomponiendo tarea con prioridad: {priority}")

    # Para due diligence siempre ejecutamos los 4 análisis
    subtasks = ["financial", "legal", "operational", "reputational"]

    out: SupervisorState = {"subtasks": subtasks}
    out.update(
        _push_event("task_decomposed", {
            "subtasks": subtasks,
            "count": len(subtasks),
        })
    )
    return out


def run_financial_worker(state: SupervisorState) -> SupervisorState:
    """Worker de análisis financiero."""
    logger.info("Ejecutando worker: financial")
    try:
        result = _run_worker_analysis(state.get("task", {}), "financial")
        worker_result = {
            "worker_type": "financial",
            "result": result,
            "status": "ok",
        }
    except Exception as e:
        logger.error(f"Error en worker financial: {e}")
        worker_result = {
            "worker_type": "financial",
            "result": {"error": str(e)},
            "status": "failed",
        }

    out: SupervisorState = {"worker_results": [worker_result]}
    out.update(_push_event("worker_completed", {"worker_type": "financial", "status": worker_result["status"]}))
    return out


def run_legal_worker(state: SupervisorState) -> SupervisorState:
    """Worker de análisis legal."""
    logger.info("Ejecutando worker: legal")
    try:
        result = _run_worker_analysis(state.get("task", {}), "legal")
        worker_result = {
            "worker_type": "legal",
            "result": result,
            "status": "ok",
        }
    except Exception as e:
        logger.error(f"Error en worker legal: {e}")
        worker_result = {
            "worker_type": "legal",
            "result": {"error": str(e)},
            "status": "failed",
        }

    out: SupervisorState = {"worker_results": [worker_result]}
    out.update(_push_event("worker_completed", {"worker_type": "legal", "status": worker_result["status"]}))
    return out


def run_operational_worker(state: SupervisorState) -> SupervisorState:
    """Worker de análisis operacional."""
    logger.info("Ejecutando worker: operational")
    try:
        result = _run_worker_analysis(state.get("task", {}), "operational")
        worker_result = {
            "worker_type": "operational",
            "result": result,
            "status": "ok",
        }
    except Exception as e:
        logger.error(f"Error en worker operational: {e}")
        worker_result = {
            "worker_type": "operational",
            "result": {"error": str(e)},
            "status": "failed",
        }

    out: SupervisorState = {"worker_results": [worker_result]}
    out.update(_push_event("worker_completed", {"worker_type": "operational", "status": worker_result["status"]}))
    return out


def run_reputational_worker(state: SupervisorState) -> SupervisorState:
    """Worker de análisis reputacional."""
    logger.info("Ejecutando worker: reputational")
    try:
        result = _run_worker_analysis(state.get("task", {}), "reputational")
        worker_result = {
            "worker_type": "reputational",
            "result": result,
            "status": "ok",
        }
    except Exception as e:
        logger.error(f"Error en worker reputational: {e}")
        worker_result = {
            "worker_type": "reputational",
            "result": {"error": str(e)},
            "status": "failed",
        }

    out: SupervisorState = {"worker_results": [worker_result]}
    out.update(_push_event("worker_completed", {"worker_type": "reputational", "status": worker_result["status"]}))
    return out


def collect_results(state: SupervisorState) -> SupervisorState:
    """
    Nodo colector: verifica que todos los workers completaron y detecta conflictos
    entre los análisis (p.ej. riesgo financiero alto vs reputación positiva).
    """
    worker_results = state.get("worker_results", []) or []
    subtasks = state.get("subtasks", []) or []
    logger.info(f"Recolectando resultados: {len(worker_results)}/{len(subtasks)} workers completados")

    # Detectar conflictos entre análisis
    conflicts: List[str] = []

    results_by_type = {r["worker_type"]: r for r in worker_results}

    fin = results_by_type.get("financial", {}).get("result", {})
    rep = results_by_type.get("reputational", {}).get("result", {})
    leg = results_by_type.get("legal", {}).get("result", {})
    ops = results_by_type.get("operational", {}).get("result", {})

    # Conflicto: riesgo financiero alto pero reputación buena
    fin_risk = float(fin.get("risk_score", 0))
    rep_sentiment = rep.get("press_sentiment", "neutral")
    if fin_risk > 7.0 and rep_sentiment == "positivo":
        conflicts.append("CONFLICTO: Alto riesgo financiero pero reputación de prensa positiva — revisar métricas")

    # Conflicto: litigios pendientes y deuda técnica alta simultáneamente
    litigations = int(leg.get("pending_litigations", 0))
    tech_debt = ops.get("tech_debt_level", "bajo")
    if litigations > 1 and tech_debt in ("alto", "crítico"):
        conflicts.append("CONFLICTO: Múltiples litigios + deuda técnica alta — riesgo de integración elevado")

    # Conflicto: dependencia de personas clave con rating Glassdoor bajo
    key_dep = ops.get("key_person_dependency", False)
    glassdoor = float(rep.get("glassdoor_rating", 5.0))
    if key_dep and glassdoor < 3.5:
        conflicts.append("CONFLICTO: Dependencia de personas clave + bajo rating Glassdoor — riesgo de fuga de talento")

    out: SupervisorState = {"conflicts": conflicts}
    out.update(
        _push_event("results_collected", {
            "workers_completed": len(worker_results),
            "conflicts_detected": len(conflicts),
        })
    )
    return out


def reconcile_and_report(state: SupervisorState) -> SupervisorState:
    """
    Nodo final del supervisor: genera el informe consolidado de due diligence
    con todos los hallazgos de los workers y los conflictos detectados.
    """
    task = state.get("task", {})
    worker_results = state.get("worker_results", []) or []
    conflicts = state.get("conflicts", []) or []

    logger.info("Generando informe consolidado de due diligence")

    results_by_type = {r["worker_type"]: r for r in worker_results}

    # Calcular score de viabilidad global (DEMO heurístico)
    scores = []
    fin = results_by_type.get("financial", {}).get("result", {})
    leg = results_by_type.get("legal", {}).get("result", {})
    ops = results_by_type.get("operational", {}).get("result", {})
    rep = results_by_type.get("reputational", {}).get("result", {})

    fin_risk = float(fin.get("risk_score", 5.0))
    fin_score = max(0, 10 - fin_risk)
    scores.append(fin_score)

    leg_score = max(0, 10 - float(leg.get("pending_litigations", 0)) * 1.5)
    scores.append(leg_score)

    tech_debt_map = {"bajo": 9, "medio": 6, "alto": 3, "crítico": 1}
    ops_score = float(tech_debt_map.get(ops.get("tech_debt_level", "medio"), 6))
    scores.append(ops_score)

    glassdoor = float(rep.get("glassdoor_rating", 3.5))
    rep_score = glassdoor * 2  # escala 1-5 -> 2-10
    scores.append(rep_score)

    global_viability = round(sum(scores) / len(scores), 2) if scores else 0.0
    conflict_penalty = len(conflicts) * 0.5
    final_viability = max(0, round(global_viability - conflict_penalty, 2))

    # Recomendación global
    if final_viability >= 7:
        recommendation = "VIABLE — Proceder con adquisición sujeto a acuerdos de mitigación"
    elif final_viability >= 4:
        recommendation = "CONDICIONAL — Revisar conflictos y negociar precio con descuento por riesgos"
    else:
        recommendation = "NO RECOMENDADO — Riesgos superan beneficios proyectados de la adquisición"

    # Consolidar flags de todos los workers
    all_flags: List[str] = []
    for wr in worker_results:
        flags = wr.get("result", {}).get("flags", []) or []
        all_flags.extend(flags)

    report = {
        "task_id": task.get("task_id"),
        "company": task.get("company"),
        "budget_usd": task.get("budget_usd"),
        "deadline": task.get("deadline"),
        "global_viability_score": final_viability,
        "recommendation": recommendation,
        "conflicts": conflicts,
        "all_flags": all_flags,
        "analyses": {
            wtype: results_by_type.get(wtype, {}).get("result", {})
            for wtype in ["financial", "legal", "operational", "reputational"]
        },
        "worker_statuses": {
            r["worker_type"]: r["status"] for r in worker_results
        },
        "mode": "DEMO",
    }

    import json as _json
    report_str = _json.dumps(report, ensure_ascii=False, indent=2)

    out: SupervisorState = {
        "final_report": report_str,
        "done": True,
    }
    out.update(
        _push_event("report_generated", {
            "viability_score": final_viability,
            "recommendation": recommendation,
            "conflicts_count": len(conflicts),
        })
    )
    return out


# ---------------------------------------------------------------------------
# Compilación del grafo
# ---------------------------------------------------------------------------

def compile_graph():
    """
    Crea y compila el StateGraph del patrón Supervisor-Workers.

    Flujo secuencial:
    load_task → decompose_task →
      run_financial_worker → run_legal_worker →
      run_operational_worker → run_reputational_worker →
    collect_results → reconcile_and_report → END
    """
    g = StateGraph(SupervisorState)

    # Nodos supervisor
    g.add_node("load_task", load_task)
    g.add_node("decompose_task", decompose_task)

    # Nodos workers (secuenciales — equivalente a paralelo en DEMO)
    g.add_node("run_financial", run_financial_worker)
    g.add_node("run_legal", run_legal_worker)
    g.add_node("run_operational", run_operational_worker)
    g.add_node("run_reputational", run_reputational_worker)

    # Nodos de consolidación
    g.add_node("collect_results", collect_results)
    g.add_node("reconcile_and_report", reconcile_and_report)

    # Edges
    g.add_edge(START, "load_task")
    g.add_edge("load_task", "decompose_task")
    g.add_edge("decompose_task", "run_financial")
    g.add_edge("run_financial", "run_legal")
    g.add_edge("run_legal", "run_operational")
    g.add_edge("run_operational", "run_reputational")
    g.add_edge("run_reputational", "collect_results")
    g.add_edge("collect_results", "reconcile_and_report")
    g.add_edge("reconcile_and_report", END)

    return g.compile(checkpointer=MemorySaver())
