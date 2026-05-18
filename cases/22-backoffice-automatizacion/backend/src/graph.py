"""
graph.py — Grafo LangGraph para el Caso 22: Backoffice — Automatización de Solicitudes.

Pipeline con 3 routers y cadena de custodia SHA-256:

  parsear_solicitud → clasificar_tipo_operacion → verificar_identidad
       → permisos_router
            ├─ sin_permisos → rechazar_solicitud → registrar_log_auditoria → END
            └─ con_permisos → validar_datos_operacion
       → completitud_router
            ├─ faltantes ∧ iter<max → solicitar_informacion → validar_datos_operacion
            └─ completos | tope → ejecutar_operacion
       → ejecucion_router
            ├─ error_sistema → escalar_soporte → registrar_log_auditoria → END
            └─ exitoso      → confirmar_solicitante → registrar_log_auditoria → END

DEMO: ejecución simulada determinista (sin red). LIVE opt-in con OPENAI_API_KEY
sólo para el resumen ejecutivo final.
"""
from __future__ import annotations

import hashlib
import json
import logging
import operator
import os
from datetime import datetime
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import (
    ejecutar_operacion_simulada,
    get_empleado,
    get_operaciones_catalog,
    get_policy,
    get_solicitud,
)
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class BackofficeState(TypedDict):
    solicitud_id: str
    solicitud: dict
    operacion: dict
    solicitante: dict
    permisos_ok: bool
    motivo_rechazo: str
    datos_completos: bool
    campos_faltantes: list
    iter_completitud: int
    resultado_ejecucion: dict
    estado_final: str
    confirmacion: str
    log_auditoria: list
    hash_auditoria: str
    resumen: str
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


def _hash_eslabon(prev_hash: str, payload: dict) -> str:
    """Cadena de custodia SHA-256 encadenada (mismo patrón que caso 06/07/15)."""
    serial = (prev_hash + "|" + json.dumps(payload, sort_keys=True, ensure_ascii=False)).encode("utf-8")
    return hashlib.sha256(serial).hexdigest()


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def parsear_solicitud(state: BackofficeState) -> dict:
    sol_id = state.get("solicitud_id", "SOL-001")
    sol = get_solicitud(sol_id, get_data_dir())

    logger.info(
        "Solicitud parseada: id=%s tipo=%s canal=%s prioridad=%s",
        sol_id, sol.get("tipo_operacion"), sol.get("canal"), sol.get("prioridad"),
    )

    return {
        "solicitud": sol,
        "iter_completitud": 0,
        "log_auditoria": [],
        "hash_auditoria": "0" * 64,
        "events": [{
            "type": "solicitud_parseada",
            "solicitud_id": sol_id,
            "canal": sol.get("canal"),
            "tipo": sol.get("tipo_operacion"),
            "prioridad": sol.get("prioridad"),
        }],
    }


def clasificar_tipo_operacion(state: BackofficeState) -> dict:
    sol = state.get("solicitud", {})
    catalog = get_operaciones_catalog(get_data_dir())
    tipo = sol.get("tipo_operacion", "")
    cfg = catalog.get(tipo, {})

    operacion = {
        "tipo": tipo,
        "sistema": cfg.get("sistema", "desconocido"),
        "endpoint": cfg.get("endpoint_simulado", ""),
        "campos_requeridos": cfg.get("campos_requeridos", []),
        "permiso_requerido": cfg.get("permiso", tipo),
        "sla_minutos": cfg.get("sla_minutos", 60),
        "conocida": bool(cfg),
    }

    logger.info(
        "Operación clasificada: tipo=%s sistema=%s conocida=%s",
        tipo, operacion["sistema"], operacion["conocida"],
    )

    return {
        "operacion": operacion,
        "events": [{
            "type": "operacion_clasificada",
            "tipo": tipo,
            "sistema": operacion["sistema"],
            "conocida": operacion["conocida"],
        }],
    }


def verificar_identidad(state: BackofficeState) -> dict:
    sol = state.get("solicitud", {})
    op = state.get("operacion", {})
    emp = get_empleado(sol.get("solicitante_id", ""), get_data_dir())

    activo = bool(emp.get("activo"))
    permiso_req = op.get("permiso_requerido", "")
    tiene_permiso = permiso_req in (emp.get("permisos", []) or [])
    permisos_ok = activo and tiene_permiso and op.get("conocida", False)

    motivo = ""
    if not emp:
        motivo = "solicitante_no_encontrado"
    elif not activo:
        motivo = "solicitante_inactivo"
    elif not op.get("conocida", False):
        motivo = "operacion_no_catalogada"
    elif not tiene_permiso:
        motivo = "sin_permiso_para_operacion"

    logger.info(
        "Identidad verificada: solicitante=%s permiso=%s ok=%s motivo=%s",
        sol.get("solicitante_id"), permiso_req, permisos_ok, motivo,
    )

    return {
        "solicitante": emp,
        "permisos_ok": permisos_ok,
        "motivo_rechazo": motivo,
        "events": [{
            "type": "identidad_verificada",
            "solicitante_id": sol.get("solicitante_id"),
            "permiso_requerido": permiso_req,
            "permisos_ok": permisos_ok,
            "motivo": motivo,
        }],
    }


def permisos_router(state: BackofficeState) -> Literal["rechazar_solicitud", "validar_datos_operacion"]:
    return "validar_datos_operacion" if state.get("permisos_ok") else "rechazar_solicitud"


def rechazar_solicitud(state: BackofficeState) -> dict:
    motivo = state.get("motivo_rechazo", "sin_permiso_para_operacion")
    sol = state.get("solicitud", {})
    confirmacion = (
        f"Solicitud {sol.get('id','')} rechazada: motivo = {motivo}. "
        f"Contacte al supervisor si considera que es un error."
    )

    logger.info("Solicitud rechazada: id=%s motivo=%s", sol.get("id"), motivo)

    return {
        "estado_final": "rechazada",
        "confirmacion": confirmacion,
        "events": [{
            "type": "solicitud_rechazada",
            "solicitud_id": sol.get("id"),
            "motivo": motivo,
        }],
    }


def validar_datos_operacion(state: BackofficeState) -> dict:
    op = state.get("operacion", {})
    sol = state.get("solicitud", {})
    datos = sol.get("datos", {}) or {}

    requeridos = op.get("campos_requeridos", [])
    faltantes = [c for c in requeridos if c not in datos or datos.get(c) in (None, "", [])]

    completos = len(faltantes) == 0

    logger.info(
        "Datos validados iter=%d: requeridos=%d faltantes=%d completos=%s",
        state.get("iter_completitud", 0), len(requeridos), len(faltantes), completos,
    )

    return {
        "datos_completos": completos,
        "campos_faltantes": faltantes,
        "events": [{
            "type": "datos_validados",
            "iter": state.get("iter_completitud", 0),
            "requeridos": len(requeridos),
            "faltantes": faltantes,
            "completos": completos,
        }],
    }


def completitud_router(state: BackofficeState) -> Literal["solicitar_informacion", "ejecutar_operacion"]:
    policy = get_policy(get_data_dir())
    max_iter = policy.get("max_iter_completitud", 2)
    if not state.get("datos_completos") and state.get("iter_completitud", 0) < max_iter:
        return "solicitar_informacion"
    return "ejecutar_operacion"


def solicitar_informacion(state: BackofficeState) -> dict:
    """Inyecta valores DEMO determinista para los campos faltantes y reintenta."""
    sol = dict(state.get("solicitud", {}))
    datos = dict(sol.get("datos", {}) or {})
    faltantes = state.get("campos_faltantes", [])

    rellenos_demo = {
        "nuevo_valor": "Av. Demo 123, Santiago",
        "motivo": "actualizacion_de_datos",
        "fecha_efectiva": "2026-06-01",
        "unidad": "comercial-general",
        "rol": "operador",
        "periodo": "2026-04",
    }
    for c in faltantes:
        datos[c] = rellenos_demo.get(c, f"valor_demo_{c}")
    sol["datos"] = datos

    iter_completitud = state.get("iter_completitud", 0) + 1
    logger.info(
        "Información solicitada iter=%d: rellenados=%s",
        iter_completitud, faltantes,
    )

    return {
        "solicitud": sol,
        "iter_completitud": iter_completitud,
        "events": [{
            "type": "informacion_solicitada",
            "iter": iter_completitud,
            "campos_rellenados": faltantes,
        }],
    }


def ejecutar_operacion(state: BackofficeState) -> dict:
    catalog = get_operaciones_catalog(get_data_dir())
    sol = state.get("solicitud", {})
    op = state.get("operacion", {})

    resultado = ejecutar_operacion_simulada(op.get("tipo", ""), sol.get("datos", {}) or {}, catalog)

    logger.info(
        "Operación ejecutada: tipo=%s ok=%s sistema=%s",
        op.get("tipo"), resultado.get("ok"), resultado.get("sistema"),
    )

    return {
        "resultado_ejecucion": resultado,
        "events": [{
            "type": "operacion_ejecutada",
            "tipo": op.get("tipo"),
            "sistema": resultado.get("sistema"),
            "ok": resultado.get("ok"),
            "referencia": resultado.get("referencia"),
            "error": resultado.get("error"),
        }],
    }


def ejecucion_router(state: BackofficeState) -> Literal["escalar_soporte", "confirmar_solicitante"]:
    return "confirmar_solicitante" if state.get("resultado_ejecucion", {}).get("ok") else "escalar_soporte"


def escalar_soporte(state: BackofficeState) -> dict:
    policy = get_policy(get_data_dir())
    sol = state.get("solicitud", {})
    res = state.get("resultado_ejecucion", {})

    mensaje = (
        f"Solicitud {sol.get('id','')} escalada a {policy.get('soporte_email','')}: "
        f"falla en sistema {res.get('sistema','?')} — {res.get('error','sin detalle')}."
    )

    logger.info(
        "Soporte escalado: id=%s sistema=%s",
        sol.get("id"), res.get("sistema"),
    )

    return {
        "estado_final": "escalada",
        "confirmacion": mensaje,
        "events": [{
            "type": "soporte_escalado",
            "solicitud_id": sol.get("id"),
            "sistema": res.get("sistema"),
            "destino": policy.get("soporte_email"),
        }],
    }


def confirmar_solicitante(state: BackofficeState) -> dict:
    sol = state.get("solicitud", {})
    res = state.get("resultado_ejecucion", {})
    op = state.get("operacion", {})

    mensaje = (
        f"Solicitud {sol.get('id','')} ejecutada exitosamente en {res.get('sistema','?')} "
        f"(referencia {res.get('referencia','—')}). SLA: {op.get('sla_minutos','?')} min."
    )

    logger.info(
        "Solicitante confirmado: id=%s ref=%s",
        sol.get("id"), res.get("referencia"),
    )

    return {
        "estado_final": "exitosa",
        "confirmacion": mensaje,
        "events": [{
            "type": "solicitante_confirmado",
            "solicitud_id": sol.get("id"),
            "referencia": res.get("referencia"),
        }],
    }


def registrar_log_auditoria(state: BackofficeState) -> dict:
    """Construye el log de auditoría inmutable (cadena SHA-256 encadenada)."""
    sol = state.get("solicitud", {})
    op = state.get("operacion", {})
    estado = state.get("estado_final", "indefinido")
    res = state.get("resultado_ejecucion", {}) or {}

    prev = "0" * 64
    log: list = []
    eventos = state.get("events", [])
    for idx, ev in enumerate(eventos):
        payload = {
            "idx": idx,
            "ts": _now_iso(),
            "solicitud_id": sol.get("id", ""),
            "type": ev.get("type", ""),
            "data": ev,
        }
        h = _hash_eslabon(prev, payload)
        log.append({**payload, "hash": h, "prev_hash": prev})
        prev = h

    metricas = {
        "estado_final": estado,
        "iter_completitud": state.get("iter_completitud", 0),
        "tipo_operacion": op.get("tipo"),
        "sistema": op.get("sistema"),
        "permisos_ok": state.get("permisos_ok", False),
        "ejecucion_ok": res.get("ok", False),
        "eslabones_log": len(log),
    }

    logger.info(
        "Log de auditoría registrado: solicitud=%s estado=%s eslabones=%d hash=%s",
        sol.get("id"), estado, len(log), prev[:12],
    )

    return {
        "log_auditoria": log,
        "hash_auditoria": prev,
        "metricas": metricas,
        "events": [{
            "type": "log_registrado",
            "solicitud_id": sol.get("id"),
            "eslabones": len(log),
            "hash_final": prev,
            "estado_final": estado,
        }],
    }


def producir_resumen(state: BackofficeState) -> dict:
    sol = state.get("solicitud", {})
    estado = state.get("estado_final", "")
    metricas = state.get("metricas", {})
    confirmacion = state.get("confirmacion", "")

    fallback = (
        f"## Resumen — Solicitud {sol.get('id','')} ({sol.get('tipo_operacion','')})\n\n"
        f"**Estado final:** {estado}\n"
        f"**Sistema:** {metricas.get('sistema','?')}\n"
        f"**Iteraciones de completitud:** {metricas.get('iter_completitud',0)}\n"
        f"**Hash final auditoría:** `{state.get('hash_auditoria','')[:16]}…`\n\n"
        f"### Mensaje al solicitante\n{confirmacion}\n\n"
        f"_Generado por agente de backoffice · Caso 22. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres jefe de backoffice. Redacta en español (máx 120 palabras) un resumen "
            f"sobre la solicitud {sol.get('id')} ({sol.get('tipo_operacion')}) "
            f"con estado final '{estado}' y {metricas.get('iter_completitud',0)} iter. "
            f"de completitud. Cierra con un próximo paso operativo."
        )
        resumen = _llm_invoke(prompt, fallback)
    else:
        resumen = fallback

    return {
        "resumen": resumen,
        "done": True,
        "events": [{
            "type": "backoffice_completado",
            "solicitud_id": sol.get("id"),
            "estado_final": estado,
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(BackofficeState)

    builder.add_node("parsear_solicitud", parsear_solicitud)
    builder.add_node("clasificar_tipo_operacion", clasificar_tipo_operacion)
    builder.add_node("verificar_identidad", verificar_identidad)
    builder.add_node("rechazar_solicitud", rechazar_solicitud)
    builder.add_node("validar_datos_operacion", validar_datos_operacion)
    builder.add_node("solicitar_informacion", solicitar_informacion)
    builder.add_node("ejecutar_operacion", ejecutar_operacion)
    builder.add_node("escalar_soporte", escalar_soporte)
    builder.add_node("confirmar_solicitante", confirmar_solicitante)
    builder.add_node("registrar_log_auditoria", registrar_log_auditoria)
    builder.add_node("producir_resumen", producir_resumen)

    builder.set_entry_point("parsear_solicitud")
    builder.add_edge("parsear_solicitud", "clasificar_tipo_operacion")
    builder.add_edge("clasificar_tipo_operacion", "verificar_identidad")

    builder.add_conditional_edges(
        "verificar_identidad",
        permisos_router,
        {
            "rechazar_solicitud": "rechazar_solicitud",
            "validar_datos_operacion": "validar_datos_operacion",
        },
    )

    builder.add_conditional_edges(
        "validar_datos_operacion",
        completitud_router,
        {
            "solicitar_informacion": "solicitar_informacion",
            "ejecutar_operacion": "ejecutar_operacion",
        },
    )
    builder.add_edge("solicitar_informacion", "validar_datos_operacion")

    builder.add_conditional_edges(
        "ejecutar_operacion",
        ejecucion_router,
        {
            "escalar_soporte": "escalar_soporte",
            "confirmar_solicitante": "confirmar_solicitante",
        },
    )

    builder.add_edge("rechazar_solicitud", "registrar_log_auditoria")
    builder.add_edge("escalar_soporte", "registrar_log_auditoria")
    builder.add_edge("confirmar_solicitante", "registrar_log_auditoria")
    builder.add_edge("registrar_log_auditoria", "producir_resumen")
    builder.add_edge("producir_resumen", END)

    return builder.compile(checkpointer=MemorySaver())
