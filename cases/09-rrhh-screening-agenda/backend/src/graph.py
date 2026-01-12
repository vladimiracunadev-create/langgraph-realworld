import json
import operator
import os
import time
from typing import Any, Annotated, Dict, List, Literal, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from .settings import data_dir, load_settings

# Integraciones reales: ver src/integrations.py (stubs)
# from .integrations import (
#    parse_resume_to_text,
#    extract_candidate_signals,
#    upsert_candidate_in_db,
#    update_ats_status,
#    create_google_calendar_event,
#    send_email_smtp_async,
#    send_email_sendgrid,
#    llm_generate_interview_questions,
# )


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
    load_settings()

    job_path = os.path.join(data_dir(), "job.json")
    candidates_path = os.path.join(data_dir(), "candidates.json")

    with open(job_path, "r", encoding="utf-8") as f:
        job = json.load(f)

    with open(candidates_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    # TODO REAL (cuando lo hagas real):
    # - Recibir CVs via /api/cv/upload o desde un bucket (S3/Drive)
    # - parse_resume_to_text(file_path) -> texto
    # - extract_candidate_signals(texto) -> skills/años/links
    # - upsert_candidate_in_db(...)
    # - update_ats_status(...)
    # - llm_generate_interview_questions(...)

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
    job = state["job"]
    candidates = state["candidates"]
    cursor = int(state.get("cursor", 0))

    if cursor >= len(candidates):
        return {}

    c = candidates[cursor]

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


def build_shortlist(state: ScreeningState) -> ScreeningState:
    """Construye shortlist a partir de los scores acumulados."""
    scored = state.get("scored", []) or []
    top_n = int(state["job"].get("top_n", 5) or 5)
    min_score = float(state["job"].get("min_score", 60) or 60)

    filtered = [x for x in scored if float(x.get("score", 0) or 0) >= min_score]
    filtered.sort(key=lambda x: float(x.get("score", 0) or 0), reverse=True)
    shortlist = filtered[:top_n]

    out: ScreeningState = {"shortlist": shortlist}
    out.update(
        _push_event(
            "shortlist",
            {"count": len(shortlist), "min_score": min_score, "top_n": top_n},
        )
    )
    return out


def schedule_interviews(state: ScreeningState) -> ScreeningState:
    """Stub de agendamiento: asigna slots de entrevista a la shortlist.

    TODO REAL:
    - create_google_calendar_event(...)
    - send_email_smtp_async(...) / send_email_sendgrid(...)
    """
    shortlist = state.get("shortlist", []) or []
    base_ts = int(time.time()) + 3600  # +1h

    scheduled: List[Dict[str, Any]] = []
    for idx, c in enumerate(shortlist):
        start_ts = base_ts + idx * 3600
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


def should_keep_scoring(state: ScreeningState) -> Literal["score_one", "build_shortlist"]:
    if state.get("cursor", 0) < len(state.get("candidates", []) or []):
        return "score_one"
    return "build_shortlist"


def compile_graph():
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

    checkpointer = SqliteSaver.from_conn_string("checkpoints.sqlite")
    return g.compile(checkpointer=checkpointer)
