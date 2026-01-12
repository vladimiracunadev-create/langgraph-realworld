import json
import os
import time
from typing import TypedDict, List, Dict, Any, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .settings import load_settings, data_dir
# Integraciones reales (stubs + guías)
from .integrations import (
    parse_resume_to_text,
    extract_candidate_signals,
    upsert_candidate_in_db,
    update_ats_status,
    create_google_calendar_event,
    send_email_smtp_async,
    send_email_sendgrid,
    llm_generate_interview_questions,
)



class ScreeningState(TypedDict, total=False):
    job: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    cursor: int
    scored: List[Dict[str, Any]]
    shortlist: List[Dict[str, Any]]
    scheduled: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    done: bool


def _push_event(kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # Reducer operator.add en el grafo hará append de eventos
    return {"events": [{"ts": time.time(), "kind": kind, **payload}]}


def load_inputs(_: ScreeningState) -> ScreeningState:
    load_settings()
    ddir = data_dir()
    # TODO REAL: reemplazar data/job.json por lectura desde tu ATS (o BD) usando httpx.
    # Ejemplo: obtener vacante por job_id desde un endpoint interno.
    with open(os.path.join(ddir, "job.json"), "r", encoding="utf-8") as f:
        job = json.load(f)
    # TODO REAL: candidatos desde CVs reales:
    # 1) Recibir archivos (endpoint /api/cv/upload) o leer desde un bucket (S3) o carpeta compartida.
    # 2) parse_resume_to_text(file_path) -> texto
    # 3) extract_candidate_signals(texto) -> skills/años/links
    # 4) upsert_candidate_in_db(...) para persistir
    with open(os.path.join(ddir, "candidates.json"), "r", encoding="utf-8") as f:
        candidates = json.load(f)

    out: ScreeningState = {
        "job": job,
        "candidates": candidates,
        "cursor": 0,
        "scored": [],
        "shortlist": [],
        "scheduled": [],
        "done": False,
    }
    out.update(_push_event("loaded", {"job_id": job.get("job_id"), "count_candidates": len(candidates)}))
    return out


def score_one(state: ScreeningState) -> ScreeningState:
    """Scoring incremental: evalúa 1 candidato por iteración para mostrar progreso en tiempo real."""
    job = state["job"]
    candidates = state["candidates"]
    i = state.get("cursor", 0)

    if i >= len(candidates):
        return {"done": True}

    c = candidates[i]
    must_have = set(job.get("must_have", []))
    nice = set(job.get("nice_to_have", []))
    skills = set(c.get("skills", []))

    scoring = job.get("scoring", {})
    must_each = int(scoring.get("must_have_each", 12))
    nice_each = int(scoring.get("nice_to_have_each", 5))
    years_w = int(scoring.get("years_experience_weight", 10))
    edu_w = int(scoring.get("education_weight", 6))
    port_w = int(scoring.get("portfolio_weight", 8))
    soft_w = int(scoring.get("soft_skills_weight", 8))
    penalty_missing = int(scoring.get("penalty_missing_must_have", 10))

    must_hits = len(must_have.intersection(skills))
    must_misses = len(must_have.difference(skills))
    nice_hits = len(nice.intersection(skills))

    years = int(c.get("years_experience", 0))
    years_score = min(years, 5) / 5 * years_w

    edu = (c.get("education") or "").lower()
    edu_score = {
        "universitario": edu_w,
        "técnico": edu_w * 0.7,
        "bootcamp": edu_w * 0.6,
        "autodidacta": edu_w * 0.45,
    }.get(edu, edu_w * 0.4)

    portfolio_score = port_w if (c.get("portfolio_url") or "").strip() else 0

    soft_skills = set(c.get("soft_skills", []))
    soft_need = set(job.get("soft_skills", []))
    soft_hits = len(soft_need.intersection(soft_skills))
    soft_score = (soft_hits / max(1, len(soft_need))) * soft_w

    base = must_hits * must_each + nice_hits * nice_each
    penalty = must_misses * penalty_missing
    total = max(0, round(base + years_score + edu_score + portfolio_score + soft_score - penalty, 2))

    result = {
        **c,
        "score": total,
        "must_hits": must_hits,
        "must_misses": must_misses,
        "nice_hits": nice_hits,
        "explain": {
            "base": base,
            "years_score": round(years_score, 2),
            "edu_score": round(edu_score, 2),
            "portfolio_score": portfolio_score,
            "soft_score": round(soft_score, 2),
            "penalty": penalty,
        },
        "status": "scored",
    }

    time.sleep(0.15)

    out: ScreeningState = {
        "cursor": i + 1,
        "scored": [result],
    }
    out.update(_push_event("scored", {"candidate_id": c["candidate_id"], "name": c["name"], "score": total}))
    return out


def build_shortlist(state: ScreeningState) -> ScreeningState:
    job = state["job"]
    scored = state.get("scored", []) or []
    min_score = float(job.get("shortlist_min_score", 55))
    top_n = int(job.get("shortlist_top_n", 4))

    ordered = sorted(scored, key=lambda x: x.get("score", 0), reverse=True)
    shortlist = [c for c in ordered if c.get("score", 0) >= min_score][:top_n]
    for c in shortlist:
        c["status"] = "shortlisted"

    out: ScreeningState = {"shortlist": shortlist}
    out.update(_push_event("shortlist", {"count": len(shortlist), "min_score": min_score, "top_n": top_n}))
    return out


def schedule_interviews(state: ScreeningState) -> ScreeningState:
    job = state["job"]
    slots = list(job.get("interview_slots", []))
    shortlist = state.get("shortlist", []) or []
    scheduled = []

    for idx, c in enumerate(shortlist):
        slot = slots[idx] if idx < len(slots) else "POR DEFINIR"
        # TODO REAL: aquí es donde lo vuelves real:
        # - create_google_calendar_event(...) para crear el evento en Calendar
        # - send_email_sendgrid(...) o send_email_smtp_async(...) para notificar
        # - update_ats_status(candidate_id, "interview_scheduled")
        item = {
            "candidate_id": c["candidate_id"],
            "name": c["name"],
            "email": c["email"],
            "slot": slot,
            "email_preview": (
                f"Hola {c['name']},\n\n"
                f"¡Gracias por postular a {job.get('title')}!\n"
                f"Te proponemos entrevista el {slot}.\n\n"
                f"Saludos,\nRR.HH."
            ),
        }
        scheduled.append(item)

    out: ScreeningState = {"scheduled": scheduled, "done": True}
    out.update(_push_event("scheduled", {"count": len(scheduled)}))
    return out


def should_keep_scoring(state: ScreeningState) -> Literal["score_one", "build_shortlist"]:
    if state.get("cursor", 0) < len(state.get("candidates", []) or []):
        return "score_one"
    return "build_shortlist"


def compile_graph():
    from typing_extensions import Annotated
    import operator

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
