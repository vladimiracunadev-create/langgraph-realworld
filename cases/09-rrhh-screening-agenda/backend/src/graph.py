import json
import logging
import operator
import os
import sqlite3
import time
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

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


class ScreeningState(BaseModel):
    """
    Estado centralizado del agente (Single Source of Truth).
    Utiliza Pydantic para validación y Annotated para definir cómo 
    se combinan los resultados de los nodos (operator.add permite acumulación).
    """
    job: Dict[str, Any] = Field(default_factory=dict)
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    cursor: int = 0
    scored: Annotated[List[Dict[str, Any]], operator.add] = Field(default_factory=list)
    shortlist: List[Dict[str, Any]] = Field(default_factory=list)
    scheduled: List[Dict[str, Any]] = Field(default_factory=list)
    events: Annotated[List[Dict[str, Any]], operator.add] = Field(default_factory=list)
    done: bool = False


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
    """
    Nodo inicial: Carga la configuración del puesto y la lista de candidatos.
    En un entorno real, esto consultaría una base de Datos SQL o un ATS.
    """
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
    """
    Nodo de procesamiento cíclico:
    1. Toma al candidato indicado por el cursor.
    2. Aplica lógica de scoring (Puntos por experiencia, educación y portafolio).
    3. Devuelve solo el cambio incremental (el score del candidato actual).
    """
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
    """
    Nodo de Acción: Agenda entrevistas para la shortlist.
    Utiliza integraciones.py para manejar la lógica híbrida (Mock vs Real Calendar).
    """
    try:
        shortlist = state.get("shortlist", []) or []
        logger.info(f"Agendando entrevistas para {len(shortlist)} candidatos")
        
        # Importación local para evitar circulares
        from .integrations import create_google_calendar_event
        
        base_ts = int(time.time()) + 86400  # Empezar mañana

        scheduled: List[Dict[str, Any]] = []
        for idx, c in enumerate(shortlist):
            start_ts = base_ts + idx * 3600
            end_ts = start_ts + 2700  # 45 min
            
            start_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(start_ts))
            end_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(end_ts))
            
            # Llamada al motor híbrido de integraciones
            res = create_google_calendar_event(
                summary=f"Entrevista Técnica: {c['name']} - {state['job'].get('title')}",
                description=f"Entrevista para evaluar skills: {c.get('skills')}",
                start_iso=start_iso,
                end_iso=end_iso,
                attendee_emails=[c.get("email", "candidato@example.com")]
            )
            
            scheduled.append({
                "candidate_id": c.get("candidate_id"),
                "name": c.get("name"),
                "slot_iso": start_iso,
                "calendar_link": res.get("html_link", "#"),
                "mode": res.get("mode"),
                "event_id": res.get("calendar_event_id")
            })

        out: ScreeningState = {"scheduled": scheduled, "done": False} # No hemos terminado aún, falta Phase 4
        out.update(_push_event("scheduled", {"count": len(scheduled)}))
        return out
    except Exception as e:
        logger.error(f"Error en agendamiento de entrevistas: {e}")
        return {
            "done": False, # Intentamos seguir a Phase 4 aunque agendamiento fallara
            "events": [{"ts": _now_ms(), "type": "error_node", "data": {"msg": str(e), "node": "schedule_interviews"}}]
        }


def notify_candidates(state: ScreeningState) -> ScreeningState:
    """
    Fase 4: Notificación.
    Envía Email y WhatsApp a los candidatos en la shortlist agendada.
    """
    try:
        scheduled = state.get("scheduled", []) or []
        logger.info(f"Notificando a {len(scheduled)} candidatos")
        
        from .integrations import send_email_notification, send_whatsapp_notification
        
        notified: List[Dict[str, Any]] = []
        for s in scheduled:
            try:
                # Encontrar el candidato original para obtener el teléfono
                candidate = next((c for c in state.get("candidates", []) if c["candidate_id"] == s["candidate_id"]), {})
                
                # 1. Enviar Email (con aislamiento)
                try:
                    email_res = send_email_notification(
                        to_email=candidate.get("email", "unknown@example.com"),
                        subject="¡Tu entrevista ha sido agendada!",
                        body=f"Hola {s['name']}, tu entrevista es el {s['slot_iso']}. Link: {s['calendar_link']}"
                    )
                    s["email_status"] = email_res["mode"]
                except Exception as e:
                    logger.error(f"Falla crítica en notificación Email para {s['name']}: {e}")
                    s["email_status"] = "FAILED_DEGRADED"

                # 2. Enviar WhatsApp (con aislamiento)
                try:
                    wa_res = send_whatsapp_notification(
                        to_phone=candidate.get("phone", "+56900000000"),
                        message=f"Hola {s['name']}, agenda confirmada: {s['slot_iso']}"
                    )
                    s["wa_status"] = wa_res["mode"]
                except Exception as e:
                    logger.error(f"Falla crítica en notificación WhatsApp para {s['name']}: {e}")
                    s["wa_status"] = "FAILED_DEGRADED"

                notified.append({
                    "candidate_id": s["candidate_id"],
                    "email_status": s["email_status"],
                    "wa_status": s["wa_status"]
                })
            except Exception as e:
                logger.error(f"Error procesando notificaciones para candidato {s.get('name')}: {e}")
                continue

        out: ScreeningState = {"scheduled": state.get("scheduled", []), "done": True} # FIN DEL CICLO
        out.update(_push_event("notified", {"count": len(notified)}))
        # Actualizamos la lista scheduled con el estado de notificación para la UI
        # (Nota: En LangGraph profesional, esto se haría acumulando en un campo 'notified' dedicado)
        return out
    except Exception as e:
        logger.error(f"Error en notify_candidates: {e}")
        return {"done": True}


def should_keep_scoring(state: ScreeningState) -> Literal["score_one", "build_shortlist"]:
    """
    Lógica de control del flujo (Router): 
    Si aún quedan candidatos por procesar, vuelve a 'score_one'.
    De lo contrario, avanza a la creación de la 'shortlist'.
    """
    if state.get("cursor", 0) < len(state.get("candidates", []) or []):
        return "score_one"
    return "build_shortlist"


def compile_graph():
    """Crea el StateGraph con acumulación de eventos y scoring incremental."""
    g = StateGraph(ScreeningState)

    g.add_node("load_inputs", load_inputs)
    g.add_node("score_one", score_one)
    g.add_node("build_shortlist", build_shortlist)
    g.add_node("schedule_interviews", schedule_interviews)
    g.add_node("notify_candidates", notify_candidates)

    g.add_edge(START, "load_inputs")
    g.add_edge("load_inputs", "score_one")
    g.add_conditional_edges("score_one", should_keep_scoring, ["score_one", "build_shortlist"])
    g.add_edge("build_shortlist", "schedule_interviews")
    g.add_edge("schedule_interviews", "notify_candidates")
    g.add_edge("notify_candidates", END)

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
