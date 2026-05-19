"""
graph.py — Grafo LangGraph para el Caso 16: Planificador de Viajes.

Pipeline con 2 routers, loop de optimización de costos y loop de ajustes del viajero:

  parsear_requisitos → verificar_politica_viajes
      ├─ política_violada → rechazar_viaje → registrar_auditoria → END
      └─ política_ok      → buscar_vuelos → buscar_alojamiento → buscar_movilidad
                          → ensamblar_itinerario → validar_presupuesto
                          → cumple_restricciones_router
                                ├─ fuera_presupuesto ∧ iter<max → optimizar_costos → ensamblar
                                └─ cumple | tope → presentar_itinerario
                          → decision_viajero_router
                                ├─ ajustar ∧ iter<max → aplicar_ajuste_iterativo → ensamblar
                                └─ aprobar | tope    → generar_brief_viaje
                          → registrar_auditoria → END

DEMO: lookup determinista sobre inventarios JSON (sin red). LIVE opt-in con
OPENAI_API_KEY sólo para el resumen ejecutivo final.
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
    buscar_hotel_optimo,
    buscar_movilidad_paquete,
    buscar_vuelo_optimo,
    get_inventario_hoteles,
    get_inventario_movilidad,
    get_inventario_vuelos,
    get_politica_viajes,
    get_viaje,
)
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())

# Descuento corporativo aplicado por `optimizar_costos` (DEMO determinista).
_DESCUENTO_OPTIMIZACION = 0.30


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class ViajeState(TypedDict):
    viaje_id: str
    requisitos: dict
    politica: dict
    politica_ok: bool
    motivo_rechazo: str
    vuelos: dict
    alojamiento: dict
    movilidad: dict
    itinerario: dict
    costo_total: int
    dentro_presupuesto: bool
    iter_optimizacion: int
    iter_ajuste: int
    decision_viajero: str
    ajuste_solicitado: str
    brief_final: str
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


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def parsear_requisitos(state: ViajeState) -> dict:
    viaje_id = state.get("viaje_id", "V-001")
    v = get_viaje(viaje_id, get_data_dir())

    requisitos = {
        "viajero": v.get("viajero", ""),
        "origen": v.get("origen", ""),
        "destino": v.get("destino", ""),
        "ciudad_destino": v.get("ciudad_destino", ""),
        "fecha_ida": v.get("fecha_ida", ""),
        "fecha_vuelta": v.get("fecha_vuelta", ""),
        "noches": int(v.get("noches", 0) or 0),
        "presupuesto_clp": int(v.get("presupuesto_clp", 0) or 0),
        "preferencias": dict(v.get("preferencias", {}) or {}),
    }
    politica = get_politica_viajes(get_data_dir())

    logger.info(
        "Requisitos parseados: viaje=%s ruta=%s-%s noches=%d presupuesto=%d",
        viaje_id, requisitos["origen"], requisitos["destino"],
        requisitos["noches"], requisitos["presupuesto_clp"],
    )

    return {
        "requisitos": requisitos,
        "politica": politica,
        "decision_viajero": v.get("decision_viajero", "aprobar"),
        "ajuste_solicitado": v.get("ajuste_solicitado", ""),
        "iter_optimizacion": 0,
        "iter_ajuste": 0,
        "audit_trail": [],
        "events": [{
            "type": "requisitos_parseados",
            "viaje_id": viaje_id,
            "ruta": f"{requisitos['origen']}-{requisitos['destino']}",
            "noches": requisitos["noches"],
            "presupuesto_clp": requisitos["presupuesto_clp"],
        }],
    }


def verificar_politica_viajes(state: ViajeState) -> dict:
    req = state.get("requisitos", {})
    pol = state.get("politica", {})
    prefs = req.get("preferencias", {}) or {}

    motivo = ""
    ciudad = (req.get("ciudad_destino", "") or "").lower()
    restringidas = [c.lower() for c in (pol.get("ciudades_restringidas", []) or [])]
    if ciudad in restringidas:
        motivo = "ciudad_restringida_por_politica"

    if not motivo:
        clase_pref = prefs.get("clase_vuelo", "economy")
        from .integrations import _CLASE_RANK  # noqa: PLC0415
        clase_max = pol.get("clase_vuelo_maxima", "economy")
        if _CLASE_RANK.get(clase_pref, 99) > _CLASE_RANK.get(clase_max, 1):
            motivo = "clase_de_vuelo_excede_politica"

    if not motivo:
        pres = int(req.get("presupuesto_clp", 0) or 0)
        max_p = int(pol.get("presupuesto_maximo_clp", 0) or 0)
        if max_p and pres > max_p:
            motivo = "presupuesto_excede_maximo_corporativo"

    politica_ok = motivo == ""

    logger.info(
        "Política verificada: ciudad=%s ok=%s motivo=%s",
        ciudad, politica_ok, motivo,
    )

    return {
        "politica_ok": politica_ok,
        "motivo_rechazo": motivo,
        "events": [{
            "type": "politica_verificada",
            "ciudad_destino": ciudad,
            "politica_ok": politica_ok,
            "motivo": motivo,
        }],
    }


def politica_router(state: ViajeState) -> Literal["rechazar_viaje", "buscar_vuelos"]:
    return "buscar_vuelos" if state.get("politica_ok") else "rechazar_viaje"


def rechazar_viaje(state: ViajeState) -> dict:
    motivo = state.get("motivo_rechazo", "violacion_politica")
    req = state.get("requisitos", {})
    mensaje = (
        f"Viaje {state.get('viaje_id','')} rechazado: {motivo}. "
        f"Destino: {req.get('ciudad_destino','')}. Contacte a Travel Manager para excepciones."
    )

    logger.info("Viaje rechazado: id=%s motivo=%s", state.get("viaje_id"), motivo)

    return {
        "estado_final": "rechazado",
        "brief_final": mensaje,
        "events": [{
            "type": "viaje_rechazado",
            "viaje_id": state.get("viaje_id"),
            "motivo": motivo,
        }],
    }


def buscar_vuelos(state: ViajeState) -> dict:
    req = state.get("requisitos", {})
    pol = state.get("politica", {})
    inv = get_inventario_vuelos(get_data_dir())
    clase_max = pol.get("clase_vuelo_maxima", "economy")

    ida = buscar_vuelo_optimo(req.get("origen", ""), req.get("destino", ""), clase_max, inv)
    vuelta = buscar_vuelo_optimo(req.get("destino", ""), req.get("origen", ""), clase_max, inv)
    # En DEMO la vuelta usa el mismo vuelo de la ruta inversa; si no existe,
    # asumimos round-trip simétrico con el mismo precio del tramo de ida.
    if not vuelta and ida:
        vuelta = {**ida, "id": ida.get("id", "") + "-R"}

    costo = (ida.get("precio_clp", 0) if ida else 0) + (vuelta.get("precio_clp", 0) if vuelta else 0)

    vuelos = {
        "ida": ida,
        "vuelta": vuelta,
        "costo_total_clp": costo,
    }

    logger.info(
        "Vuelos buscados: ida=%s vuelta=%s costo=%d",
        ida.get("id"), vuelta.get("id"), costo,
    )

    return {
        "vuelos": vuelos,
        "events": [{
            "type": "vuelos_buscados",
            "ida_id": ida.get("id"),
            "vuelta_id": vuelta.get("id"),
            "costo_total_clp": costo,
        }],
    }


def buscar_alojamiento(state: ViajeState) -> dict:
    req = state.get("requisitos", {})
    pol = state.get("politica", {})
    inv = get_inventario_hoteles(get_data_dir())
    prefs = req.get("preferencias", {}) or {}

    cat_min = int(prefs.get("categoria_hotel_min", 3) or 3)
    cat_max = int(pol.get("categoria_hotel_maxima", 4) or 4)
    # Si el viajero pidió mayor categoría, respetar dentro del techo corporativo
    if cat_min > cat_max:
        cat_min = cat_max

    hotel = buscar_hotel_optimo(req.get("ciudad_destino", ""), cat_min, cat_max, inv)
    noches = int(req.get("noches", 0) or 0)
    subtotal = (hotel.get("tarifa_noche_clp", 0) if hotel else 0) * noches

    alojamiento = {
        "hotel": hotel,
        "noches": noches,
        "costo_total_clp": subtotal,
    }

    logger.info(
        "Alojamiento buscado: hotel=%s noches=%d costo=%d",
        hotel.get("id"), noches, subtotal,
    )

    return {
        "alojamiento": alojamiento,
        "events": [{
            "type": "alojamiento_buscado",
            "hotel_id": hotel.get("id"),
            "categoria": hotel.get("categoria"),
            "noches": noches,
            "costo_total_clp": subtotal,
        }],
    }


def buscar_movilidad(state: ViajeState) -> dict:
    req = state.get("requisitos", {})
    inv = get_inventario_movilidad(get_data_dir())
    paquete = buscar_movilidad_paquete(req.get("ciudad_destino", ""), int(req.get("noches", 0) or 0), inv)

    logger.info(
        "Movilidad buscada: ciudad=%s items=%d costo=%d",
        req.get("ciudad_destino"), len(paquete.get("items", [])), paquete.get("costo_total_clp", 0),
    )

    return {
        "movilidad": paquete,
        "events": [{
            "type": "movilidad_buscada",
            "ciudad": req.get("ciudad_destino"),
            "items": len(paquete.get("items", [])),
            "costo_total_clp": paquete.get("costo_total_clp", 0),
        }],
    }


def ensamblar_itinerario(state: ViajeState) -> dict:
    vuelos = state.get("vuelos", {}) or {}
    alojamiento = state.get("alojamiento", {}) or {}
    movilidad = state.get("movilidad", {}) or {}

    costo_vuelos = int(vuelos.get("costo_total_clp", 0) or 0)
    costo_aloj = int(alojamiento.get("costo_total_clp", 0) or 0)
    costo_mov = int(movilidad.get("costo_total_clp", 0) or 0)

    descuento_factor = (1.0 - _DESCUENTO_OPTIMIZACION) ** int(state.get("iter_optimizacion", 0) or 0)
    costo_total = int(round((costo_vuelos + costo_aloj + costo_mov) * descuento_factor))

    itinerario = {
        "vuelos": vuelos,
        "alojamiento": alojamiento,
        "movilidad": movilidad,
        "desglose_clp": {
            "vuelos": costo_vuelos,
            "alojamiento": costo_aloj,
            "movilidad": costo_mov,
            "subtotal_bruto": costo_vuelos + costo_aloj + costo_mov,
            "descuento_corporativo_pct": round((1.0 - descuento_factor) * 100, 1),
            "total_final": costo_total,
        },
    }

    logger.info(
        "Itinerario ensamblado: vuelos=%d aloj=%d mov=%d desc=%.2f total=%d",
        costo_vuelos, costo_aloj, costo_mov, 1.0 - descuento_factor, costo_total,
    )

    return {
        "itinerario": itinerario,
        "costo_total": costo_total,
        "events": [{
            "type": "itinerario_ensamblado",
            "costo_total_clp": costo_total,
            "descuento_pct": round((1.0 - descuento_factor) * 100, 1),
        }],
    }


def validar_presupuesto(state: ViajeState) -> dict:
    presupuesto = int(state.get("requisitos", {}).get("presupuesto_clp", 0) or 0)
    costo = int(state.get("costo_total", 0) or 0)
    dentro = costo <= presupuesto and presupuesto > 0

    logger.info(
        "Presupuesto validado: costo=%d presupuesto=%d dentro=%s",
        costo, presupuesto, dentro,
    )

    return {
        "dentro_presupuesto": dentro,
        "events": [{
            "type": "presupuesto_validado",
            "costo_total_clp": costo,
            "presupuesto_clp": presupuesto,
            "dentro_presupuesto": dentro,
        }],
    }


def cumple_restricciones_router(state: ViajeState) -> Literal["optimizar_costos", "presentar_itinerario"]:
    pol = state.get("politica", {})
    max_iter = int(pol.get("max_iter_optimizacion", 2) or 2)
    if state.get("dentro_presupuesto"):
        return "presentar_itinerario"
    if int(state.get("iter_optimizacion", 0) or 0) >= max_iter:
        return "presentar_itinerario"
    return "optimizar_costos"


def optimizar_costos(state: ViajeState) -> dict:
    """Incrementa el contador de optimización; el descuento se reaplica en `ensamblar`."""
    nueva_iter = int(state.get("iter_optimizacion", 0) or 0) + 1

    logger.info(
        "Optimización aplicada iter=%d (descuento corporativo %.0f%% por iter)",
        nueva_iter, _DESCUENTO_OPTIMIZACION * 100,
    )

    return {
        "iter_optimizacion": nueva_iter,
        "events": [{
            "type": "optimizacion_aplicada",
            "iter": nueva_iter,
            "descuento_pct": _DESCUENTO_OPTIMIZACION * 100,
        }],
    }


def presentar_itinerario(state: ViajeState) -> dict:
    costo = state.get("costo_total", 0)
    dentro = state.get("dentro_presupuesto", False)

    logger.info(
        "Itinerario presentado: costo=%d dentro_presupuesto=%s decision=%s",
        costo, dentro, state.get("decision_viajero"),
    )

    return {
        "events": [{
            "type": "itinerario_presentado",
            "costo_total_clp": costo,
            "dentro_presupuesto": dentro,
            "decision_viajero": state.get("decision_viajero"),
        }],
    }


def decision_viajero_router(state: ViajeState) -> Literal["aplicar_ajuste_iterativo", "generar_brief_viaje"]:
    pol = state.get("politica", {})
    max_iter = int(pol.get("max_iter_ajuste", 2) or 2)
    decision = state.get("decision_viajero", "aprobar")
    iter_aj = int(state.get("iter_ajuste", 0) or 0)
    # Una vez aplicado al menos un ajuste, el viajero aprueba (DEMO determinista).
    if decision == "aprobar" or iter_aj >= max_iter or iter_aj >= 1:
        return "generar_brief_viaje"
    return "aplicar_ajuste_iterativo"


def aplicar_ajuste_iterativo(state: ViajeState) -> dict:
    """Aplica el ajuste solicitado por el viajero (DEMO: sube categoría de hotel)."""
    req = dict(state.get("requisitos", {}))
    prefs = dict(req.get("preferencias", {}) or {})
    ajuste = state.get("ajuste_solicitado", "") or ""

    if "categoria 4" in ajuste.lower() or "hotel" in ajuste.lower():
        prefs["categoria_hotel_min"] = max(int(prefs.get("categoria_hotel_min", 3) or 3), 4)
    req["preferencias"] = prefs
    nueva_iter = int(state.get("iter_ajuste", 0) or 0) + 1

    logger.info(
        "Ajuste aplicado iter=%d: '%s' -> prefs=%s",
        nueva_iter, ajuste, prefs,
    )

    return {
        "requisitos": req,
        "iter_ajuste": nueva_iter,
        # Reset del loop de optimización porque el itinerario cambia
        "iter_optimizacion": 0,
        "events": [{
            "type": "ajuste_aplicado",
            "iter": nueva_iter,
            "ajuste_solicitado": ajuste,
            "preferencias": prefs,
        }],
    }


def generar_brief_viaje(state: ViajeState) -> dict:
    req = state.get("requisitos", {})
    it = state.get("itinerario", {}) or {}
    desglose = it.get("desglose_clp", {}) or {}
    vuelos = it.get("vuelos", {}) or {}
    aloj = it.get("alojamiento", {}) or {}

    fallback = (
        f"## Itinerario — {req.get('viajero','')} ({state.get('viaje_id','')})\n\n"
        f"**Ruta:** {req.get('origen','')} ⇄ {req.get('destino','')} "
        f"({req.get('fecha_ida','')} → {req.get('fecha_vuelta','')})\n"
        f"**Vuelos:** ida `{vuelos.get('ida',{}).get('id','—')}`, "
        f"vuelta `{vuelos.get('vuelta',{}).get('id','—')}`\n"
        f"**Hotel:** {aloj.get('hotel',{}).get('nombre','—')} "
        f"(cat. {aloj.get('hotel',{}).get('categoria','?')}, {aloj.get('noches',0)} noches)\n"
        f"**Costo total final:** CLP {desglose.get('total_final',0):,}\n"
        f"**Descuento corporativo aplicado:** {desglose.get('descuento_corporativo_pct',0)}%\n"
        f"**Iteraciones:** optimización={state.get('iter_optimizacion',0)}, "
        f"ajuste={state.get('iter_ajuste',0)}\n\n"
        f"_Brief generado por agente de viajes · Caso 16. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres travel manager corporativo. Redacta en español (≤120 palabras) un brief "
            f"profesional para el viaje de {req.get('viajero')} "
            f"({req.get('origen')}→{req.get('destino')}, {req.get('noches',0)} noches), "
            f"costo final CLP {desglose.get('total_final',0):,}. "
            f"Incluye próximo paso (reservar / comunicar al viajero)."
        )
        brief = _llm_invoke(prompt, fallback)
    else:
        brief = fallback

    logger.info(
        "Brief generado: viaje=%s costo=%d",
        state.get("viaje_id"), desglose.get("total_final", 0),
    )

    return {
        "estado_final": "aprobado",
        "brief_final": brief,
        "events": [{
            "type": "brief_generado",
            "viaje_id": state.get("viaje_id"),
            "costo_total_clp": desglose.get("total_final", 0),
        }],
    }


def registrar_auditoria(state: ViajeState) -> dict:
    """Audit trail simple (no regulatorio): timestamps + tipo de evento + viaje_id."""
    viaje_id = state.get("viaje_id", "")
    estado = state.get("estado_final", "indefinido")
    eventos = state.get("events", [])

    audit = [
        {
            "idx": idx,
            "ts": _now_iso(),
            "viaje_id": viaje_id,
            "type": ev.get("type", ""),
            "data": ev,
        }
        for idx, ev in enumerate(eventos)
    ]

    desglose = (state.get("itinerario", {}) or {}).get("desglose_clp", {}) or {}
    metricas = {
        "estado_final": estado,
        "iter_optimizacion": int(state.get("iter_optimizacion", 0) or 0),
        "iter_ajuste": int(state.get("iter_ajuste", 0) or 0),
        "costo_total_clp": int(state.get("costo_total", 0) or 0),
        "presupuesto_clp": int(state.get("requisitos", {}).get("presupuesto_clp", 0) or 0),
        "descuento_pct": desglose.get("descuento_corporativo_pct", 0),
        "politica_ok": bool(state.get("politica_ok", False)),
        "eventos_totales": len(audit),
    }

    logger.info(
        "Auditoría registrada: viaje=%s estado=%s eventos=%d",
        viaje_id, estado, len(audit),
    )

    return {
        "audit_trail": audit,
        "metricas": metricas,
        "done": True,
        "events": [{
            "type": "auditoria_registrada",
            "viaje_id": viaje_id,
            "estado_final": estado,
            "eventos_totales": len(audit),
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(ViajeState)

    builder.add_node("parsear_requisitos", parsear_requisitos)
    builder.add_node("verificar_politica_viajes", verificar_politica_viajes)
    builder.add_node("rechazar_viaje", rechazar_viaje)
    builder.add_node("buscar_vuelos", buscar_vuelos)
    builder.add_node("buscar_alojamiento", buscar_alojamiento)
    builder.add_node("buscar_movilidad", buscar_movilidad)
    builder.add_node("ensamblar_itinerario", ensamblar_itinerario)
    builder.add_node("validar_presupuesto", validar_presupuesto)
    builder.add_node("optimizar_costos", optimizar_costos)
    builder.add_node("presentar_itinerario", presentar_itinerario)
    builder.add_node("aplicar_ajuste_iterativo", aplicar_ajuste_iterativo)
    builder.add_node("generar_brief_viaje", generar_brief_viaje)
    builder.add_node("registrar_auditoria", registrar_auditoria)

    builder.set_entry_point("parsear_requisitos")
    builder.add_edge("parsear_requisitos", "verificar_politica_viajes")

    builder.add_conditional_edges(
        "verificar_politica_viajes",
        politica_router,
        {
            "rechazar_viaje": "rechazar_viaje",
            "buscar_vuelos": "buscar_vuelos",
        },
    )

    builder.add_edge("buscar_vuelos", "buscar_alojamiento")
    builder.add_edge("buscar_alojamiento", "buscar_movilidad")
    builder.add_edge("buscar_movilidad", "ensamblar_itinerario")
    builder.add_edge("ensamblar_itinerario", "validar_presupuesto")

    builder.add_conditional_edges(
        "validar_presupuesto",
        cumple_restricciones_router,
        {
            "optimizar_costos": "optimizar_costos",
            "presentar_itinerario": "presentar_itinerario",
        },
    )
    builder.add_edge("optimizar_costos", "ensamblar_itinerario")

    builder.add_conditional_edges(
        "presentar_itinerario",
        decision_viajero_router,
        {
            "aplicar_ajuste_iterativo": "aplicar_ajuste_iterativo",
            "generar_brief_viaje": "generar_brief_viaje",
        },
    )
    builder.add_edge("aplicar_ajuste_iterativo", "buscar_alojamiento")

    builder.add_edge("rechazar_viaje", "registrar_auditoria")
    builder.add_edge("generar_brief_viaje", "registrar_auditoria")
    builder.add_edge("registrar_auditoria", END)

    return builder.compile(checkpointer=MemorySaver())
