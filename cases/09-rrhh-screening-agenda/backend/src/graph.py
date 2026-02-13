import json
import logging
import operator
import os
import sqlite3
import time
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from .settings import checkpoint_db_path, data_dir, load_settings

logger = logging.getLogger(__name__)

_SQLITE_CONN: sqlite3.Connection | None = None


def _get_sqlite_conn(db_path: str) -> sqlite3.Connection:
    """Crea/reutiliza conexión SQLite (instancia real, no context-manager)."""
    global _SQLITE_CONN
    if _SQLITE_CONN is not None:
        return _SQLITE_CONN

    # Asegura carpeta (cuando no es :memory:)
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    _SQLITE_CONN = sqlite3.connect(db_path, check_same_thread=False)
    return _SQLITE_CONN


class ScreeningState(TypedDict, total=False):
    job: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    cursor: int
    scored: List[Dict[str, Any]]
    shortlist: List[Dict[str, Any]]
    scheduled: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    done: bool


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


def load_inputs(state: ScreeningState) -> ScreeningState:
    """Carga job + candidates desde data/ para que el demo sea determinista."""
    logger.info("Cargando inputs para el screening")
    load_settings()

    job_path = os.path.join(data_dir(), "job.json")
    candidates_path = os.path.join(data_dir(), "candidates.json")

    with open(job_path, "r", encoding="utf-8") as f:
        job = json.load(f)

    with open(candidates_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    out: ScreeningState = {
        "job": job,
        "candidates": candidates,
        "cursor": 0,
        "scored": [],
        "shortlist": [],
        "scheduled": [],
        "events": state.get("events", []) or [],
        "done": False,
    }
    out.update(
        _push_event(
            "loaded",
            {"job_id": job.get("job_id"), "count_candidates": len(candidates)},
        )
    )
    return out


def score_one(state: ScreeningState) -> ScreeningState:
    """Scoring incremental: evalúa 1 candidato por iteración para mostrar progreso."""
    try:
        job = state["job"]
        candidates = state["candidates"]
        cursor = int(state.get("cursor", 0))

        if cursor >= len(candidates):
            return {}

        c = candidates[cursor]
        logger.info(f"Evaluando candidato: {c.get('name')} (cursor: {cursor})")

        # El scoring actual es determinístico, pero si fuera una llamada a LLM...
        must = job.get("must_have", []) or []
        nice = job.get("nice_to_have", []) or []
        min_years = float(job.get("min_years", 0) or 0)

        c_skills = [s.lower() for s in (c.get("skills") or [])]
        must_hits = sum(1 for s in must if s.lower() in c_skills)
        nice_hits = sum(1 for s in nice if s.lower() in c_skills)

        must_each = 15.0
        nice_each = 5.0
        penalty_missing = 12.0

        must_misses = max(0, len(must) - must_hits)
        years = float(c.get("years_experience", 0) or 0)

        years_score = 0.0
        if min_years > 0:
            years_score = min(20.0, max(0.0, (years - min_years) * 5.0 + 10.0))

        edu = (c.get("education") or "").lower()
        edu_score = 10.0 if any(x in edu for x in ["ing", "engineer", "informat", "cs"]) else 4.0

        portfolio = (c.get("portfolio_url") or "").strip()
        portfolio_score = 8.0 if portfolio else 0.0

        soft = [s.lower() for s in (c.get("soft_skills") or [])]
        soft_score = 2.0 * min(5, len(soft))

        base = must_hits * must_each + nice_hits * nice_each
        penalty = must_misses * penalty_missing
        total = max(0, round(base + years_score + edu_score + portfolio_score + soft_score - penalty, 2))

        result = {
            "candidate_id": c.get("candidate_id"),
            "name": c.get("name"),
            "email": c.get("email"),
            "score": total,
            "must_hits": must_hits,
            "nice_hits": nice_hits,
            "years": years,
            "portfolio_url": portfolio,
        }

        out: ScreeningState = {
            "cursor": cursor + 1,
            "scored": [result],
        }
        out.update(
            _push_event(
                "scored",
                {"candidate_id": c.get("candidate_id"), "name": c.get("name"), "score": total},
            )
        )
        return out
    except Exception as e:
        logger.error(f"Error procesando candidato en cursor {state.get('cursor')}: {e}")
        # Degradación graciosa: saltar candidato y marcar error
        return {
            "cursor": state.get("cursor", 0) + 1,
            "events": [{"ts": _now_ms(), "type": "error_node", "data": {"msg": str(e), "node": "score_one"}}]
        }


def build_shortlist(state: ScreeningState) -> ScreeningState:
    """Construye shortlist a partir de los scores acumulados."""
    scored = state.get("scored", []) or []
    top_n = int(state["job"].get("top_n", 5) or 5)
    min_score = float(state["job"].get("min_score", 60) or 60)

    filtered = [x for x in scored if float(x.get("score", 0) or 0) >= min_score]
    filtered.sort(key=lambda x: float(x.get("score", 0) or 0), reverse=True)
    shortlist = filtered[:top_n]

    out: ScreeningState = {"shortlist": shortlist}
    out.update(_push_event("shortlist", {"count": len(shortlist), "min_score": min_score, "top_n": top_n}))
    return out


def schedule_interviews(state: ScreeningState) -> ScreeningState:
    """Stub de agendamiento: asigna slots de entrevista a la shortlist."""
    try:
        shortlist = state.get("shortlist", []) or []
        logger.info(f"Agendando entrevistas para {len(shortlist)} candidatos")
        
        base_ts = int(time.time()) + 3600  # +1h

        scheduled: List[Dict[str, Any]] = []
        for idx, c in enumerate(shortlist):
            start_ts = base_ts + idx * 3600
            
            # Simulamos que esto podría llamar a una API real (Google Calendar / SMTP)
            # a través de las funciones en integrations.py (que ya tienen reintentos)
            
            scheduled.append(
                {
                    "candidate_id": c.get("candidate_id"),
                    "name": c.get("name"),
                    "email": c.get("email"),
                    "slot_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(start_ts)),
                    "duration_min": 45,
                    "status": "stub_scheduled",
                }
            )

        out: ScreeningState = {"scheduled": scheduled, "done": True}
        out.update(_push_event("scheduled", {"count": len(scheduled)}))
        return out
    except Exception as e:
        logger.error(f"Error en agendamiento de entrevistas: {e}")
        return {
            "done": True, # Marcamos como hecho aunque fallara el agendamiento (degradación)
            "events": [{"ts": _now_ms(), "type": "error_node", "data": {"msg": str(e), "node": "schedule_interviews"}}]
        }


def should_keep_scoring(state: ScreeningState) -> Literal["score_one", "build_shortlist"]:
    if state.get("cursor", 0) < len(state.get("candidates", []) or []):
        return "score_one"
    return "build_shortlist"


def compile_graph():
    """Crea el StateGraph con acumulación de eventos y scoring incremental."""
    class State(TypedDict, total=False):
        job: Dict[str, Any]
        candidates: List[Dict[str, Any]]
        cursor: int
        scored: Annotated[List[Dict[str, Any]], operator.add]
        shortlist: List[Dict[str, Any]]
        scheduled: List[Dict[str, Any]]
        events: Annotated[List[Dict[str, Any]], operator.add]
        done: bool

    g = StateGraph(State)

    g.add_node("load_inputs", load_inputs)
    g.add_node("score_one", score_one)
    g.add_node("build_shortlist", build_shortlist)
    g.add_node("schedule_interviews", schedule_interviews)

    g.add_edge(START, "load_inputs")
    g.add_edge("load_inputs", "score_one")
    g.add_conditional_edges("score_one", should_keep_scoring, ["score_one", "build_shortlist"])
    g.add_edge("build_shortlist", "schedule_interviews")
    g.add_edge("schedule_interviews", END)

    db_path = checkpoint_db_path()

    # Si alguien desactiva checkpoints con CHECKPOINT_DB=none/false, compila sin checkpointer
    if not db_path or db_path.lower() in {"none", "false", "0"}:
        return g.compile(checkpointer=None)

    conn = _get_sqlite_conn(db_path)
    checkpointer = SqliteSaver(conn)

    # RECURSION_LIMIT: Guardrail básico de LangGraph
    # En este caso, 1 (load) + 1 (shortlist) + 1 (schedule) + N (candidates)
    # Ponemos un margen seguro.
    return g.compile(checkpointer=checkpointer)
