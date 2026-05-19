"""
graph.py — Grafo LangGraph para Caso 23: Salud — Pre-triage Administrativo.

ATENCIÓN REGULATORIA: Este flujo realiza CLASIFICACIÓN ADMINISTRATIVA de la consulta
del paciente. NO emite diagnóstico médico ni indicación terapéutica. Todas las
respuestas hacia el paciente incluyen un disclaimer explícito que separa la
clasificación administrativa del acto médico.

Pipeline:

  bienvenida_y_datos_basicos
   → recopilar_motivo_consulta
   → preguntar_sintomas_referidos
   → recopilar_antecedentes_relevantes
   → verificar_cobertura_documentacion
   → clasificar_nivel_urgencia
        → router_nivel_urgencia
            ├─ cobertura_pendiente → derivar_documentacion_pendiente
            ├─ inmediata           → derivar_urgencias
            ├─ programable         → derivar_especialidad
            └─ teleconsulta        → derivar_teleconsulta
   → generar_resumen_derivacion → registrar_sesion → END

DEMO: clasificación determinista basada en `protocolo_urgencia.json`.
LIVE opt-in (OPENAI_API_KEY) sólo humaniza el resumen de derivación.
"""
from __future__ import annotations

import logging
import operator
import os
from datetime import datetime
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import (
    get_especialidades,
    get_policy,
    get_protocolo,
    get_sesion,
)
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())

DISCLAIMER_DEFAULT = (
    "Esta clasificación es administrativa y no constituye diagnóstico ni "
    "indicación médica. Ante síntomas graves contacte al servicio de urgencias."
)


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class PretriageState(TypedDict):
    sesion_id: str
    paciente: dict
    motivo_consulta: str
    sintomas: list
    antecedentes: dict
    cobertura_ok: bool
    documentacion_faltante: list
    nivel_urgencia: str
    puntaje_urgencia: int
    derivacion: dict
    resumen_derivacion: str
    disclaimer: str
    estado_final: str
    audit_trail: list
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


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _disclaimer() -> str:
    policy = get_policy(get_data_dir())
    return policy.get("disclaimer_obligatorio", DISCLAIMER_DEFAULT)


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def bienvenida_y_datos_basicos(state: PretriageState) -> dict:
    sid = state.get("sesion_id", "S-001")
    sesion = get_sesion(sid, get_data_dir())
    paciente = sesion.get("paciente", {}) or {}

    logger.info(
        "Bienvenida: sesion=%s paciente=%s edad=%s",
        sid, paciente.get("nombre"), paciente.get("edad"),
    )

    return {
        "paciente": paciente,
        "disclaimer": _disclaimer(),
        "audit_trail": [{"ts": _now_iso(), "nodo": "bienvenida_y_datos_basicos", "sesion": sid}],
        "events": [{
            "type": "bienvenida",
            "sesion_id": sid,
            "canal": sesion.get("canal"),
            "paciente_nombre": paciente.get("nombre"),
        }],
    }


def recopilar_motivo_consulta(state: PretriageState) -> dict:
    sid = state.get("sesion_id", "S-001")
    sesion = get_sesion(sid, get_data_dir())
    motivo = (sesion.get("motivo_consulta") or "").strip()

    logger.info("Motivo recopilado: sesion=%s motivo=%r", sid, motivo)

    return {
        "motivo_consulta": motivo,
        "audit_trail": [{"ts": _now_iso(), "nodo": "recopilar_motivo_consulta", "motivo": motivo}],
        "events": [{
            "type": "motivo_consulta_recopilado",
            "motivo": motivo,
        }],
    }


def preguntar_sintomas_referidos(state: PretriageState) -> dict:
    sid = state.get("sesion_id", "S-001")
    sesion = get_sesion(sid, get_data_dir())
    sintomas = list(sesion.get("sintomas") or [])

    logger.info("Síntomas referidos: sesion=%s sintomas=%s", sid, sintomas)

    return {
        "sintomas": sintomas,
        "audit_trail": [{"ts": _now_iso(), "nodo": "preguntar_sintomas_referidos", "sintomas": sintomas}],
        "events": [{
            "type": "sintomas_recopilados",
            "cantidad": len(sintomas),
            "sintomas": sintomas,
        }],
    }


def recopilar_antecedentes_relevantes(state: PretriageState) -> dict:
    sid = state.get("sesion_id", "S-001")
    sesion = get_sesion(sid, get_data_dir())
    antecedentes = dict(sesion.get("antecedentes") or {})

    logger.info(
        "Antecedentes: sesion=%s meds=%d alergias=%d comorbil=%d",
        sid,
        len(antecedentes.get("medicamentos", []) or []),
        len(antecedentes.get("alergias", []) or []),
        len(antecedentes.get("comorbilidades", []) or []),
    )

    return {
        "antecedentes": antecedentes,
        "audit_trail": [{"ts": _now_iso(), "nodo": "recopilar_antecedentes_relevantes"}],
        "events": [{
            "type": "antecedentes_recopilados",
            "medicamentos": antecedentes.get("medicamentos", []),
            "alergias": antecedentes.get("alergias", []),
            "comorbilidades": antecedentes.get("comorbilidades", []),
        }],
    }


def verificar_cobertura_documentacion(state: PretriageState) -> dict:
    policy = get_policy(get_data_dir())
    requeridos = policy.get("documentos_requeridos", [])
    docs = list((state.get("paciente") or {}).get("documentacion") or [])
    faltantes = [d for d in requeridos if d not in docs]
    cobertura_ok = len(faltantes) == 0

    logger.info(
        "Cobertura verificada: ok=%s faltantes=%s",
        cobertura_ok, faltantes,
    )

    return {
        "cobertura_ok": cobertura_ok,
        "documentacion_faltante": faltantes,
        "audit_trail": [{
            "ts": _now_iso(), "nodo": "verificar_cobertura_documentacion",
            "ok": cobertura_ok, "faltantes": faltantes,
        }],
        "events": [{
            "type": "cobertura_verificada",
            "ok": cobertura_ok,
            "faltantes": faltantes,
        }],
    }


def _puntaje_edad(edad: int, factores: list) -> int:
    for rango in factores:
        if rango.get("min", 0) <= edad <= rango.get("max", 200):
            return int(rango.get("puntaje", 0))
    return 0


def _detectar_especialidad(motivo: str, sintomas: list, mapping: dict) -> str:
    """Mapeo administrativo motivo/síntoma → especialidad. Determinista."""
    haystack = " ".join([motivo or ""] + (sintomas or [])).lower()
    for clave, esp in mapping.items():
        if clave.lower() in haystack:
            return esp
    return "medicina_general"


def clasificar_nivel_urgencia(state: PretriageState) -> dict:
    """
    Reglas ADMINISTRATIVAS deterministas (no medicina): suma de puntajes
    de protocolo configurable. NO emite diagnóstico ni indicación clínica.
    """
    policy = get_policy(get_data_dir())
    protocolo = get_protocolo(get_data_dir())

    if not state.get("cobertura_ok"):
        return {
            "nivel_urgencia": "cobertura_pendiente",
            "puntaje_urgencia": 0,
            "audit_trail": [{
                "ts": _now_iso(), "nodo": "clasificar_nivel_urgencia",
                "nivel": "cobertura_pendiente", "puntaje": 0,
            }],
            "events": [{
                "type": "clasificacion_administrativa",
                "nivel": "cobertura_pendiente",
                "puntaje": 0,
            }],
        }

    sintomas = state.get("sintomas") or []
    antec = state.get("antecedentes") or {}
    paciente = state.get("paciente") or {}
    motivo = (state.get("motivo_consulta") or "").lower()

    sint_pesos = protocolo.get("sintomas_criticos", {}) or {}
    puntaje = sum(int(sint_pesos.get(s, 0)) for s in sintomas)

    edad = int(paciente.get("edad", 0) or 0)
    puntaje += _puntaje_edad(edad, protocolo.get("factores_edad", []) or [])

    comorbil_pesos = protocolo.get("comorbilidades_riesgo", {}) or {}
    for c in (antec.get("comorbilidades") or []):
        puntaje += int(comorbil_pesos.get(c, 0))

    motivos_tele = [m.lower() for m in (protocolo.get("motivos_teleconsulta", []) or [])]
    motivos_prog = protocolo.get("motivos_programables_especialidad", {}) or {}

    umbral_inm = int(policy.get("umbral_urgencia_inmediata", 70))
    umbral_tel = int(policy.get("umbral_teleconsulta", 30))

    if puntaje >= umbral_inm:
        nivel = "inmediata"
    elif any(m in motivo for m in motivos_tele):
        nivel = "teleconsulta"
    elif any(k.lower() in motivo for k in motivos_prog.keys()) or any(
        s in motivos_prog for s in sintomas
    ):
        nivel = "programable"
    elif puntaje <= umbral_tel:
        nivel = "teleconsulta"
    else:
        nivel = "programable"

    logger.info(
        "Clasificación administrativa: nivel=%s puntaje=%d (sin diagnóstico médico)",
        nivel, puntaje,
    )

    return {
        "nivel_urgencia": nivel,
        "puntaje_urgencia": puntaje,
        "audit_trail": [{
            "ts": _now_iso(), "nodo": "clasificar_nivel_urgencia",
            "nivel": nivel, "puntaje": puntaje,
        }],
        "events": [{
            "type": "clasificacion_administrativa",
            "nivel": nivel,
            "puntaje": puntaje,
            "nota": "clasificacion_administrativa_sin_diagnostico",
        }],
    }


def nivel_urgencia_router(
    state: PretriageState,
) -> Literal[
    "derivar_documentacion_pendiente",
    "derivar_urgencias",
    "derivar_especialidad",
    "derivar_teleconsulta",
]:
    nivel = state.get("nivel_urgencia", "")
    if nivel == "cobertura_pendiente":
        return "derivar_documentacion_pendiente"
    if nivel == "inmediata":
        return "derivar_urgencias"
    if nivel == "programable":
        return "derivar_especialidad"
    return "derivar_teleconsulta"


def derivar_documentacion_pendiente(state: PretriageState) -> dict:
    faltantes = state.get("documentacion_faltante", [])
    derivacion = {
        "servicio": "admision_documentacion",
        "profesional_sugerido": "Ejecutivo de Admisión",
        "agenda": "presencial — ventanilla de admisión",
        "modalidad": "presencial",
        "instrucciones": (
            "Antes de la consulta, regularice la documentación faltante: "
            + ", ".join(faltantes)
        ),
    }
    logger.info("Derivación admin: documentación pendiente faltantes=%s", faltantes)
    return {
        "derivacion": derivacion,
        "estado_final": "derivado_documentacion_pendiente",
        "audit_trail": [{
            "ts": _now_iso(), "nodo": "derivar_documentacion_pendiente",
            "faltantes": faltantes,
        }],
        "events": [{
            "type": "derivacion_emitida",
            "servicio": derivacion["servicio"],
            "faltantes": faltantes,
        }],
    }


def derivar_urgencias(state: PretriageState) -> dict:
    esps = get_especialidades(get_data_dir())
    cfg = esps.get("urgencias", {})
    derivacion = {
        "servicio": "urgencias",
        "profesional_sugerido": cfg.get("profesional_sugerido", "Equipo de Urgencias"),
        "agenda": cfg.get("agenda_proxima", "inmediata"),
        "modalidad": cfg.get("modalidad", "presencial"),
        "instrucciones": (
            "Acudir de inmediato a la unidad de urgencias del centro asistencial "
            "más cercano. Si no puede trasladarse por sus medios, contacte al SAMU (131)."
        ),
    }
    logger.info("Derivación admin: URGENCIAS puntaje=%s", state.get("puntaje_urgencia"))
    return {
        "derivacion": derivacion,
        "estado_final": "derivado_urgencias",
        "audit_trail": [{"ts": _now_iso(), "nodo": "derivar_urgencias"}],
        "events": [{
            "type": "derivacion_emitida",
            "servicio": derivacion["servicio"],
        }],
    }


def derivar_especialidad(state: PretriageState) -> dict:
    esps = get_especialidades(get_data_dir())
    protocolo = get_protocolo(get_data_dir())
    mapping = protocolo.get("motivos_programables_especialidad", {}) or {}

    esp = _detectar_especialidad(
        state.get("motivo_consulta", ""),
        state.get("sintomas", []) or [],
        mapping,
    )
    cfg = esps.get(esp, esps.get("medicina_general", {}))

    derivacion = {
        "servicio": esp,
        "profesional_sugerido": cfg.get("profesional_sugerido", "Médico General"),
        "agenda": cfg.get("agenda_proxima", ""),
        "modalidad": cfg.get("modalidad", "presencial"),
        "instrucciones": (
            "Reserva administrativa de turno en la especialidad indicada. "
            "Esta asignación es administrativa; el profesional evaluará y "
            "definirá la conducta clínica."
        ),
    }
    logger.info("Derivación admin: especialidad=%s", esp)
    return {
        "derivacion": derivacion,
        "estado_final": "derivado_especialidad",
        "audit_trail": [{
            "ts": _now_iso(), "nodo": "derivar_especialidad", "especialidad": esp,
        }],
        "events": [{
            "type": "derivacion_emitida",
            "servicio": esp,
        }],
    }


def derivar_teleconsulta(state: PretriageState) -> dict:
    esps = get_especialidades(get_data_dir())
    cfg = esps.get("teleconsulta_general", {})
    derivacion = {
        "servicio": "teleconsulta_general",
        "profesional_sugerido": cfg.get("profesional_sugerido", "Médico telemedicina"),
        "agenda": cfg.get("agenda_proxima", ""),
        "modalidad": cfg.get("modalidad", "telemedicina"),
        "instrucciones": (
            "Se agenda teleconsulta como vía administrativa adecuada para su "
            "motivo de consulta. La evaluación clínica completa la realiza el "
            "profesional durante la videollamada."
        ),
    }
    logger.info("Derivación admin: TELECONSULTA puntaje=%s", state.get("puntaje_urgencia"))
    return {
        "derivacion": derivacion,
        "estado_final": "derivado_teleconsulta",
        "audit_trail": [{"ts": _now_iso(), "nodo": "derivar_teleconsulta"}],
        "events": [{
            "type": "derivacion_emitida",
            "servicio": derivacion["servicio"],
        }],
    }


def generar_resumen_derivacion(state: PretriageState) -> dict:
    paciente = state.get("paciente") or {}
    der = state.get("derivacion") or {}
    nivel = state.get("nivel_urgencia", "")
    puntaje = state.get("puntaje_urgencia", 0)
    disclaimer = state.get("disclaimer") or _disclaimer()

    fallback = (
        f"## Resumen de derivación administrativa — sesión {state.get('sesion_id','')}\n\n"
        f"**Paciente:** {paciente.get('nombre','—')} "
        f"(edad {paciente.get('edad','?')}, DNI {paciente.get('dni','?')})\n"
        f"**Cobertura:** {paciente.get('cobertura','—')}\n"
        f"**Motivo declarado:** {state.get('motivo_consulta','—')}\n"
        f"**Síntomas referidos:** {', '.join(state.get('sintomas',[]) or []) or '—'}\n"
        f"**Clasificación administrativa:** {nivel} (puntaje {puntaje})\n"
        f"**Servicio asignado:** {der.get('servicio','—')} · "
        f"Profesional sugerido: {der.get('profesional_sugerido','—')}\n"
        f"**Agenda:** {der.get('agenda','—')} ({der.get('modalidad','—')})\n\n"
        f"### Instrucciones administrativas\n{der.get('instrucciones','—')}\n\n"
        f"> {disclaimer}\n\n"
        f"_Generado por agente de pre-triage administrativo · Caso 23. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres asistente administrativo de salud (NO médico). Redacta en español "
            f"un resumen de la derivación administrativa para sesión {state.get('sesion_id','')}, "
            f"paciente {paciente.get('nombre','')} edad {paciente.get('edad','')}. "
            f"Clasificación: {nivel}, servicio {der.get('servicio','')}. "
            f"NO uses palabras como 'diagnóstico', 'indicación médica' fuera de mencionar "
            f"que NO se emite ninguna. Cierra con este disclaimer textual: \"{disclaimer}\""
        )
        resumen = _llm_invoke(prompt, fallback)
    else:
        resumen = fallback

    return {
        "resumen_derivacion": resumen,
        "audit_trail": [{"ts": _now_iso(), "nodo": "generar_resumen_derivacion"}],
        "events": [{
            "type": "resumen_generado",
            "nivel": nivel,
            "servicio": der.get("servicio"),
        }],
    }


def registrar_sesion(state: PretriageState) -> dict:
    nivel = state.get("nivel_urgencia", "")
    estado = state.get("estado_final", "")
    metricas = {
        "sesion_id": state.get("sesion_id", ""),
        "nivel_urgencia": nivel,
        "puntaje_urgencia": state.get("puntaje_urgencia", 0),
        "cobertura_ok": bool(state.get("cobertura_ok", False)),
        "documentos_faltantes": len(state.get("documentacion_faltante", []) or []),
        "servicio_asignado": (state.get("derivacion") or {}).get("servicio", ""),
        "modo": "LIVE" if _LIVE_MODE else "DEMO",
        "eventos_totales": len(state.get("events", []) or []) + 1,
        "estado_final": estado,
    }
    logger.info(
        "Sesión registrada: sesion=%s nivel=%s estado=%s servicio=%s",
        state.get("sesion_id"), nivel, estado, metricas["servicio_asignado"],
    )
    return {
        "metricas": metricas,
        "done": True,
        "audit_trail": [{"ts": _now_iso(), "nodo": "registrar_sesion"}],
        "events": [{
            "type": "sesion_registrada",
            "sesion_id": state.get("sesion_id"),
            "estado_final": estado,
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(PretriageState)

    builder.add_node("bienvenida_y_datos_basicos", bienvenida_y_datos_basicos)
    builder.add_node("recopilar_motivo_consulta", recopilar_motivo_consulta)
    builder.add_node("preguntar_sintomas_referidos", preguntar_sintomas_referidos)
    builder.add_node("recopilar_antecedentes_relevantes", recopilar_antecedentes_relevantes)
    builder.add_node("verificar_cobertura_documentacion", verificar_cobertura_documentacion)
    builder.add_node("clasificar_nivel_urgencia", clasificar_nivel_urgencia)
    builder.add_node("derivar_documentacion_pendiente", derivar_documentacion_pendiente)
    builder.add_node("derivar_urgencias", derivar_urgencias)
    builder.add_node("derivar_especialidad", derivar_especialidad)
    builder.add_node("derivar_teleconsulta", derivar_teleconsulta)
    builder.add_node("generar_resumen_derivacion", generar_resumen_derivacion)
    builder.add_node("registrar_sesion", registrar_sesion)

    builder.set_entry_point("bienvenida_y_datos_basicos")
    builder.add_edge("bienvenida_y_datos_basicos", "recopilar_motivo_consulta")
    builder.add_edge("recopilar_motivo_consulta", "preguntar_sintomas_referidos")
    builder.add_edge("preguntar_sintomas_referidos", "recopilar_antecedentes_relevantes")
    builder.add_edge("recopilar_antecedentes_relevantes", "verificar_cobertura_documentacion")
    builder.add_edge("verificar_cobertura_documentacion", "clasificar_nivel_urgencia")

    builder.add_conditional_edges(
        "clasificar_nivel_urgencia",
        nivel_urgencia_router,
        {
            "derivar_documentacion_pendiente": "derivar_documentacion_pendiente",
            "derivar_urgencias": "derivar_urgencias",
            "derivar_especialidad": "derivar_especialidad",
            "derivar_teleconsulta": "derivar_teleconsulta",
        },
    )

    for n in (
        "derivar_documentacion_pendiente",
        "derivar_urgencias",
        "derivar_especialidad",
        "derivar_teleconsulta",
    ):
        builder.add_edge(n, "generar_resumen_derivacion")

    builder.add_edge("generar_resumen_derivacion", "registrar_sesion")
    builder.add_edge("registrar_sesion", END)

    return builder.compile(checkpointer=MemorySaver())
