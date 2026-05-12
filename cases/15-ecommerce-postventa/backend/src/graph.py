"""
graph.py — Grafo LangGraph para el Caso 15: E-commerce Postventa.

Pipeline reactivo con 3 routers:

  recibir_solicitud → lookup_pedido → clasificar_intencion
                                              │
                  ┌───────────────────────────┼──────────────────────────┐
            seguimiento                  devolucion                   cambio
                  │                          │                            │
                  ▼                          ▼                            ▼
          consultar_tracking      verificar_elegibilidad         verificar_stock
                  │                  {router elegibilidad}     {router stock}
                  │              ┌───────┴────────┐         ┌────────┴────────┐
                  │           elegible       no_elegible disponible       agotado
                  │              │                │         │                │
                  │              ▼                ▼         ▼                ▼
                  │     generar_etiqueta   derivar_humano  procesar_cambio derivar_humano
                  │              │                │         │                │
                  └──────────────┴────────────────┴─────────┴────────────────┘
                                              ↓
                                       redactar_respuesta → producir_resumen → END

Etiqueta de devolución con trazabilidad SHA-256 sobre payload canonicalizado.
LIVE opt-in con OPENAI_API_KEY para redacción empática de la respuesta al cliente.
"""
from __future__ import annotations

import hashlib
import json
import logging
import operator
import os
from datetime import date, datetime
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import get_inventory, get_order, get_policy, stock_disponible
from .settings import data_dir as get_data_dir
from .settings import fecha_hoy_iso

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())

_INTENT_VALID = {"seguimiento", "devolucion", "cambio"}


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class PostventaState(TypedDict):
    order_id: str
    intent_input: str
    pedido: dict
    intencion: str
    tracking: dict
    elegibilidad: dict
    etiqueta: dict
    stock: dict
    cambio_resultado: dict
    escalacion: dict
    respuesta: str
    resumen: str
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

def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _today() -> date:
    parsed = _parse_date(fecha_hoy_iso())
    return parsed or date.today()


def _days_between(start_iso: str, end: date) -> int | None:
    start = _parse_date(start_iso)
    if not start:
        return None
    return (end - start).days


def _label_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def recibir_solicitud(state: PostventaState) -> dict:
    order_id = state.get("order_id", "")
    intent_input = (state.get("intent_input") or "").strip().lower()
    logger.info("Solicitud postventa recibida: order_id=%s intent_input=%s", order_id, intent_input or "(auto)")
    return {
        "events": [{
            "type": "solicitud_recibida",
            "order_id": order_id,
            "intent_input": intent_input or None,
        }],
    }


def lookup_pedido(state: PostventaState) -> dict:
    order_id = state.get("order_id", "")
    pedido = get_order(order_id, get_data_dir())
    encontrado = pedido.get("estado") != "no_encontrado" and bool(pedido.get("id"))

    logger.info(
        "Pedido cargado: id=%s cliente=%s estado=%s items=%d",
        pedido.get("id"), pedido.get("cliente", "—"),
        pedido.get("estado"), len(pedido.get("items", [])),
    )

    return {
        "pedido": pedido,
        "events": [{
            "type": "pedido_consultado",
            "order_id": pedido.get("id"),
            "cliente": pedido.get("cliente"),
            "estado": pedido.get("estado"),
            "encontrado": encontrado,
            "items": len(pedido.get("items", [])),
        }],
    }


def clasificar_intencion(state: PostventaState) -> dict:
    """Toma intent_input si es válido; si no, usa el intent del pedido (DEMO)."""
    intent_input = (state.get("intent_input") or "").strip().lower()
    pedido = state.get("pedido", {})
    intent_pedido = (pedido.get("intent") or "").strip().lower()

    if intent_input in _INTENT_VALID:
        intencion = intent_input
        fuente = "cliente"
    elif intent_pedido in _INTENT_VALID:
        intencion = intent_pedido
        fuente = "pedido"
    else:
        intencion = "seguimiento"
        fuente = "default"

    logger.info("Intención clasificada: %s (fuente=%s)", intencion, fuente)

    return {
        "intencion": intencion,
        "events": [{
            "type": "intencion_clasificada",
            "intencion": intencion,
            "fuente": fuente,
        }],
    }


# Router 1: intención

def intencion_router(state: PostventaState) -> str:
    intencion = state.get("intencion", "seguimiento")
    if intencion in _INTENT_VALID:
        return intencion
    return "seguimiento"


# --- Camino: seguimiento ----------------------------------------------------

def consultar_tracking(state: PostventaState) -> dict:
    pedido = state.get("pedido", {})
    tracking = pedido.get("tracking", {}) or {}
    estado = pedido.get("estado", "")
    info = {
        "encontrado": bool(tracking),
        "codigo": tracking.get("codigo"),
        "carrier": pedido.get("carrier"),
        "ubicacion": tracking.get("ubicacion"),
        "eta": tracking.get("eta"),
        "ultima_actualizacion": tracking.get("ultima_actualizacion"),
        "hitos": tracking.get("hitos", []),
        "estado_pedido": estado,
    }

    logger.info(
        "Tracking consultado: codigo=%s estado=%s eta=%s",
        info["codigo"], estado, info["eta"],
    )

    return {
        "tracking": info,
        "events": [{
            "type": "tracking_consultado",
            "codigo": info["codigo"],
            "estado_pedido": estado,
            "eta": info["eta"],
            "hitos": len(info["hitos"]),
        }],
    }


# --- Camino: devolución -----------------------------------------------------

def verificar_elegibilidad(state: PostventaState) -> dict:
    pedido = state.get("pedido", {})
    policy = get_policy(get_data_dir())
    plazo = int(policy.get("plazo_devolucion_dias", 30))
    no_devolvibles = set(policy.get("categorias_no_devolvibles", []))

    fecha_entrega = pedido.get("fecha_entrega") or pedido.get("fecha_compra")
    dias = _days_between(fecha_entrega, _today())
    dias = dias if dias is not None else 999

    items = pedido.get("items", []) or []
    categorias_bloqueadas = [it for it in items if it.get("categoria") in no_devolvibles]

    razones: list = []
    if pedido.get("estado") != "entregado":
        razones.append(f"Pedido no está entregado (estado: {pedido.get('estado', '—')})")
    if dias > plazo:
        razones.append(f"Plazo excedido ({dias} días desde entrega, máximo {plazo})")
    if categorias_bloqueadas:
        nombres = ", ".join(it.get("nombre", it.get("sku", "")) for it in categorias_bloqueadas)
        razones.append(f"Categoría no devolvible: {nombres}")

    elegible = len(razones) == 0
    elegibilidad = {
        "elegible": elegible,
        "dias_desde_entrega": dias,
        "plazo_permitido": plazo,
        "razones": razones,
        "policy_version": policy.get("etiqueta_prefix", "RET"),
    }

    logger.info(
        "Elegibilidad devolución: elegible=%s dias=%d razones=%d",
        elegible, dias, len(razones),
    )

    return {
        "elegibilidad": elegibilidad,
        "events": [{
            "type": "elegibilidad_evaluada",
            "elegible": elegible,
            "dias": dias,
            "razones": razones,
        }],
    }


def elegibilidad_router(state: PostventaState) -> str:
    return "elegible" if state.get("elegibilidad", {}).get("elegible", False) else "no_elegible"


def generar_etiqueta(state: PostventaState) -> dict:
    pedido = state.get("pedido", {})
    policy = get_policy(get_data_dir())
    today = _today().strftime("%Y-%m-%d")

    payload = {
        "etiqueta_id": f"{policy.get('etiqueta_prefix', 'RET')}-{pedido.get('id', '')}-{today.replace('-', '')}",
        "order_id": pedido.get("id"),
        "cliente": pedido.get("cliente"),
        "carrier": policy.get("carrier_devolucion", "BlueExpress"),
        "monto_a_reembolsar": pedido.get("monto_total", 0),
        "fecha_emision": today,
        "items_a_retornar": [
            {"sku": it.get("sku"), "nombre": it.get("nombre"), "cantidad": it.get("cantidad", 1)}
            for it in pedido.get("items", [])
        ],
        "max_dias_procesamiento": int(policy.get("max_dias_procesamiento", 5)),
    }
    payload["sha256"] = _label_hash(payload)

    logger.info(
        "Etiqueta generada: id=%s carrier=%s hash=%s",
        payload["etiqueta_id"], payload["carrier"], payload["sha256"],
    )

    return {
        "etiqueta": {"emitida": True, **payload},
        "events": [{
            "type": "etiqueta_emitida",
            "etiqueta_id": payload["etiqueta_id"],
            "carrier": payload["carrier"],
            "monto_reembolso": payload["monto_a_reembolsar"],
            "hash": payload["sha256"],
        }],
    }


# --- Camino: cambio ---------------------------------------------------------

def verificar_stock(state: PostventaState) -> dict:
    pedido = state.get("pedido", {})
    policy = get_policy(get_data_dir())
    plazo_cambio = int(policy.get("plazo_cambio_dias", 15))

    fecha_entrega = pedido.get("fecha_entrega") or pedido.get("fecha_compra")
    dias = _days_between(fecha_entrega, _today())
    dias = dias if dias is not None else 999

    items = pedido.get("items", []) or []
    detalle: list = []
    todos_disponibles = True
    for it in items:
        destino = it.get("sku_destino") or it.get("sku")
        cantidad = int(it.get("cantidad", 1) or 1)
        disponible = stock_disponible(destino, get_data_dir())
        ok = disponible >= cantidad
        if not ok:
            todos_disponibles = False
        detalle.append({
            "sku_origen": it.get("sku"),
            "sku_destino": destino,
            "cantidad_solicitada": cantidad,
            "stock_disponible": disponible,
            "ok": ok,
        })

    fuera_plazo = dias > plazo_cambio

    stock = {
        "todos_disponibles": todos_disponibles and not fuera_plazo,
        "dias_desde_entrega": dias,
        "plazo_permitido": plazo_cambio,
        "fuera_plazo": fuera_plazo,
        "detalle": detalle,
    }

    logger.info(
        "Stock verificado: todos_ok=%s fuera_plazo=%s items=%d",
        stock["todos_disponibles"], fuera_plazo, len(detalle),
    )

    return {
        "stock": stock,
        "events": [{
            "type": "stock_verificado",
            "todos_disponibles": stock["todos_disponibles"],
            "fuera_plazo": fuera_plazo,
            "items_ok": sum(1 for d in detalle if d["ok"]),
            "items_total": len(detalle),
        }],
    }


def stock_router(state: PostventaState) -> str:
    return "disponible" if state.get("stock", {}).get("todos_disponibles", False) else "agotado"


def procesar_cambio(state: PostventaState) -> dict:
    pedido = state.get("pedido", {})
    inv = get_inventory(get_data_dir())
    today = _today().strftime("%Y-%m-%d")

    reservas: list = []
    for d in state.get("stock", {}).get("detalle", []):
        destino = d.get("sku_destino")
        meta = inv.get(destino, {})
        reservas.append({
            "sku_destino": destino,
            "nombre": meta.get("nombre", destino),
            "cantidad": d.get("cantidad_solicitada", 1),
            "ubicacion": meta.get("ubicacion", "—"),
            "reserva_id": f"RES-{pedido.get('id', '')}-{destino}",
        })

    resultado = {
        "exitoso": True,
        "order_id": pedido.get("id"),
        "fecha_proceso": today,
        "reservas": reservas,
        "carrier_envio": "BlueExpress",
        "eta_envio_dias": 3,
    }

    logger.info(
        "Cambio procesado: order=%s reservas=%d",
        pedido.get("id"), len(reservas),
    )

    return {
        "cambio_resultado": resultado,
        "events": [{
            "type": "cambio_procesado",
            "order_id": pedido.get("id"),
            "reservas": len(reservas),
        }],
    }


# --- Convergencia: derivar a humano ----------------------------------------

def derivar_humano(state: PostventaState) -> dict:
    """Convergencia de caminos no-felices (no elegible, agotado, plazo excedido)."""
    intencion = state.get("intencion", "")
    razones: list = []
    if intencion == "devolucion":
        razones = list(state.get("elegibilidad", {}).get("razones", []))
        motivo = "Devolución no procede automáticamente"
    elif intencion == "cambio":
        stock = state.get("stock", {})
        if stock.get("fuera_plazo"):
            razones.append(f"Plazo de cambio excedido ({stock.get('dias_desde_entrega')} días, máx {stock.get('plazo_permitido')})")
        for d in stock.get("detalle", []):
            if not d.get("ok"):
                razones.append(
                    f"SKU destino {d.get('sku_destino')} sin stock suficiente "
                    f"(disponible {d.get('stock_disponible')}, requerido {d.get('cantidad_solicitada')})"
                )
        motivo = "Cambio requiere intervención humana"
    else:
        motivo = "Caso requiere revisión"

    escalacion = {
        "requerida": True,
        "intencion": intencion,
        "motivo": motivo,
        "razones": razones,
        "asignado_a": "equipo_postventa_l2",
        "sla_horas": 24,
    }

    logger.info("Escalación a humano: motivo=%s razones=%d", motivo, len(razones))

    return {
        "escalacion": escalacion,
        "events": [{
            "type": "escalado_humano",
            "intencion": intencion,
            "razones": razones,
            "sla_horas": 24,
        }],
    }


# --- Cierre: respuesta + resumen -------------------------------------------

def redactar_respuesta(state: PostventaState) -> dict:
    pedido = state.get("pedido", {})
    intencion = state.get("intencion", "")
    tracking = state.get("tracking", {})
    elegib = state.get("elegibilidad", {})
    etiqueta = state.get("etiqueta", {})
    stock = state.get("stock", {})
    cambio = state.get("cambio_resultado", {})
    escal = state.get("escalacion", {})

    cliente = pedido.get("cliente", "estimado/a cliente")

    if intencion == "seguimiento" and tracking.get("encontrado"):
        fallback = (
            f"Hola {cliente}, tu pedido {pedido.get('id')} está en estado "
            f"**{pedido.get('estado', '—')}**. Última actualización: "
            f"{tracking.get('ubicacion', '—')} ({tracking.get('ultima_actualizacion', '—')}). "
            f"Fecha estimada de entrega: **{tracking.get('eta', '—')}**. "
            f"Código de seguimiento {tracking.get('codigo', '—')} en {tracking.get('carrier') or pedido.get('carrier', '—')}."
        )
    elif intencion == "devolucion" and etiqueta.get("emitida"):
        fallback = (
            f"Hola {cliente}, tu devolución ha sido aprobada. Hemos generado la etiqueta "
            f"**{etiqueta.get('etiqueta_id')}** ({etiqueta.get('carrier')}). El reembolso estimado es de "
            f"${etiqueta.get('monto_a_reembolsar', 0):,} CLP y se procesará en hasta "
            f"{etiqueta.get('max_dias_procesamiento')} días hábiles tras recibir el producto en bodega."
        )
    elif intencion == "cambio" and cambio.get("exitoso"):
        items_txt = ", ".join(
            f"{r.get('nombre', r.get('sku_destino'))}" for r in cambio.get("reservas", [])
        )
        fallback = (
            f"Hola {cliente}, hemos procesado tu cambio para el pedido {pedido.get('id')}. "
            f"Reservamos: {items_txt}. El nuevo despacho saldrá vía {cambio.get('carrier_envio')} "
            f"y la entrega estimada es en {cambio.get('eta_envio_dias')} días hábiles."
        )
    elif escal.get("requerida"):
        razones_txt = "; ".join(escal.get("razones", [])) or "tu caso requiere revisión"
        fallback = (
            f"Hola {cliente}, lamentablemente no podemos procesar automáticamente tu solicitud "
            f"de **{intencion}** sobre el pedido {pedido.get('id')}. Motivo: {razones_txt}. "
            f"Hemos derivado tu caso a nuestro equipo de postventa nivel 2; te contactarán "
            f"dentro de las próximas {escal.get('sla_horas', 24)} horas."
        )
    else:
        fallback = (
            f"Hola {cliente}, hemos recibido tu solicitud para el pedido {pedido.get('id', '—')}. "
            f"Un agente revisará tu caso y te contactaremos a la brevedad."
        )

    if _LIVE_MODE:
        prompt = (
            "Eres agente de postventa de un e-commerce chileno. Redacta una respuesta empática "
            f"en español (máx 120 palabras) para el cliente {cliente} sobre su solicitud de "
            f"{intencion} para el pedido {pedido.get('id')}. "
            f"Hechos a comunicar: {fallback}. Mantén un tono cercano, profesional y útil. "
            "Cierra con un saludo y referencia a futuro contacto si aplica."
        )
        respuesta = _llm_invoke(prompt, fallback)
    else:
        respuesta = fallback

    logger.info("Respuesta redactada: intencion=%s len=%d", intencion, len(respuesta))

    return {
        "respuesta": respuesta,
        "events": [{
            "type": "respuesta_redactada",
            "intencion": intencion,
            "len": len(respuesta),
        }],
    }


def producir_resumen(state: PostventaState) -> dict:
    pedido = state.get("pedido", {})
    intencion = state.get("intencion", "")
    etiqueta = state.get("etiqueta", {})
    cambio = state.get("cambio_resultado", {})
    escal = state.get("escalacion", {})

    if escal.get("requerida"):
        resultado_icon = "🟡"
        resultado = "DERIVADO"
    elif etiqueta.get("emitida") or cambio.get("exitoso") or state.get("tracking", {}).get("encontrado"):
        resultado_icon = "🟢"
        resultado = "RESUELTO"
    else:
        resultado_icon = "🔴"
        resultado = "INCOMPLETO"

    resumen = (
        f"## Caso de postventa — {pedido.get('id', '—')}\n\n"
        f"**Cliente:** {pedido.get('cliente', '—')} ({pedido.get('email', '—')})\n"
        f"**Intención:** {intencion}\n"
        f"**Resultado:** {resultado_icon} {resultado}\n\n"
        f"### Acciones automatizadas\n"
        f"- Tracking consultado: {'sí' if state.get('tracking', {}).get('encontrado') else 'no'}\n"
        f"- Elegibilidad evaluada: {'sí (' + ('elegible' if state.get('elegibilidad', {}).get('elegible') else 'no elegible') + ')' if state.get('elegibilidad') else 'no aplica'}\n"
        f"- Etiqueta emitida: {etiqueta.get('etiqueta_id') if etiqueta.get('emitida') else 'no'}\n"
        f"- Cambio procesado: {'sí (' + str(len(cambio.get('reservas', []))) + ' reservas)' if cambio.get('exitoso') else 'no'}\n"
        f"- Escalación humana: {'sí — ' + str(len(escal.get('razones', []))) + ' razones' if escal.get('requerida') else 'no'}\n\n"
        f"_Caso procesado por agente postventa — Caso 15. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    logger.info(
        "Caso completado: order=%s intencion=%s resultado=%s",
        pedido.get("id"), intencion, resultado,
    )

    return {
        "resumen": resumen,
        "done": True,
        "events": [{
            "type": "caso_completado",
            "order_id": pedido.get("id"),
            "intencion": intencion,
            "resultado": resultado,
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(PostventaState)

    builder.add_node("recibir_solicitud", recibir_solicitud)
    builder.add_node("lookup_pedido", lookup_pedido)
    builder.add_node("clasificar_intencion", clasificar_intencion)
    builder.add_node("consultar_tracking", consultar_tracking)
    builder.add_node("verificar_elegibilidad", verificar_elegibilidad)
    builder.add_node("generar_etiqueta", generar_etiqueta)
    builder.add_node("verificar_stock", verificar_stock)
    builder.add_node("procesar_cambio", procesar_cambio)
    builder.add_node("derivar_humano", derivar_humano)
    builder.add_node("redactar_respuesta", redactar_respuesta)
    builder.add_node("producir_resumen", producir_resumen)

    builder.set_entry_point("recibir_solicitud")
    builder.add_edge("recibir_solicitud", "lookup_pedido")
    builder.add_edge("lookup_pedido", "clasificar_intencion")

    builder.add_conditional_edges(
        "clasificar_intencion",
        intencion_router,
        {
            "seguimiento": "consultar_tracking",
            "devolucion": "verificar_elegibilidad",
            "cambio": "verificar_stock",
        },
    )

    builder.add_edge("consultar_tracking", "redactar_respuesta")

    builder.add_conditional_edges(
        "verificar_elegibilidad",
        elegibilidad_router,
        {"elegible": "generar_etiqueta", "no_elegible": "derivar_humano"},
    )
    builder.add_edge("generar_etiqueta", "redactar_respuesta")

    builder.add_conditional_edges(
        "verificar_stock",
        stock_router,
        {"disponible": "procesar_cambio", "agotado": "derivar_humano"},
    )
    builder.add_edge("procesar_cambio", "redactar_respuesta")
    builder.add_edge("derivar_humano", "redactar_respuesta")

    builder.add_edge("redactar_respuesta", "producir_resumen")
    builder.add_edge("producir_resumen", END)

    return builder.compile(checkpointer=MemorySaver())
