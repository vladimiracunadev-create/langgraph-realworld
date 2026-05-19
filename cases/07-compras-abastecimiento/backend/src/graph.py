"""
graph.py — Grafo LangGraph para el Caso 07: Compras y Abastecimiento.

Pipeline de adquisición:
  validar_solicitud → buscar_proveedores → lanzar_rfq → recopilar_cotizaciones
    → comparar_ofertas → {router politica_compras}
        ├─ dentro_politica → recomendar_proveedor ┐
        └─ requiere_comite → escalar_comite       ┴→ recomendar_proveedor
                                                       ↓
                            aprobacion_responsable → generar_orden_compra → producir_resumen → END

Score multi-criterio determinista (precio 40 / plazo 30 / riesgo proveedor 30) sobre el
catálogo homologado. El router activa el comité cuando el monto supera el umbral o el
proveedor recomendado no está en la lista preferida. LIVE opt-in con OPENAI_API_KEY para
justificación contractual y resumen ejecutivo del comprador.
"""
from __future__ import annotations

import hashlib
import json
import logging
import operator
import os
from datetime import datetime
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import get_policy, get_scenario, get_suppliers
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class CompraState(TypedDict):
    solicitud_id: str
    centro_costo: str
    presupuesto_max: float
    categoria: str
    descripcion: str
    items: list
    fecha_requerida: str
    responsable: str
    pr_validada: dict
    suppliers_candidatos: list
    rfqs_emitidas: list
    cotizaciones_recibidas: list
    comparativa: list
    decision_politica: dict
    escalacion_comite: dict
    recomendacion: dict
    aprobacion: dict
    orden_compra: dict
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

def _today_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _po_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _score_quote(quote: dict, supplier: dict, weights: dict, presupuesto_max: float) -> dict:
    """
    Score 0-100 multi-criterio:
      - precio:  100 * (1 - precio/presupuesto_max),    clamp 0..100
      - plazo:   100 - (plazo_dias * 100 / max_plazo),  clamp 0..100   (max_plazo=30)
      - riesgo:  100 - (riesgo_proveedor * 100)         (riesgo_proveedor 0..1)
    """
    precio = float(quote.get("precio_total", 0) or 0)
    plazo = int(quote.get("plazo_dias", 30) or 30)
    riesgo = float(supplier.get("riesgo", 0.5) or 0.5)
    riesgo = max(0.0, min(1.0, riesgo))

    if presupuesto_max <= 0:
        score_precio = 0.0
    else:
        score_precio = max(0.0, min(100.0, 100.0 * (1.0 - (precio / presupuesto_max))))

    max_plazo = 30
    score_plazo = max(0.0, min(100.0, 100.0 - (plazo * 100.0 / max_plazo)))
    score_riesgo = max(0.0, min(100.0, 100.0 * (1.0 - riesgo)))

    score_total = (
        score_precio * weights.get("precio", 0.4)
        + score_plazo * weights.get("plazo", 0.3)
        + score_riesgo * weights.get("riesgo", 0.3)
    )

    return {
        "score_precio": round(score_precio, 1),
        "score_plazo": round(score_plazo, 1),
        "score_riesgo": round(score_riesgo, 1),
        "score_total": round(score_total, 1),
    }


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def validar_solicitud(state: CompraState) -> dict:
    """Carga el escenario y valida completitud de la PR."""
    solicitud_id = state.get("solicitud_id", "PR-001")
    sc = get_scenario(solicitud_id, get_data_dir())

    items = sc.get("items", [])
    presupuesto = float(sc.get("presupuesto_max", 0) or 0)

    faltantes: list = []
    if not sc.get("centro_costo"):
        faltantes.append("centro_costo")
    if presupuesto <= 0:
        faltantes.append("presupuesto_max")
    if not items:
        faltantes.append("items")
    if not sc.get("categoria"):
        faltantes.append("categoria")

    valida = len(faltantes) == 0
    monto_estimado = sum(float(it.get("precio_estimado", 0) or 0) * int(it.get("cantidad", 1) or 1) for it in items)

    pr_validada = {
        "valida": valida,
        "faltantes": faltantes,
        "monto_estimado": round(monto_estimado, 0),
        "supera_presupuesto": monto_estimado > presupuesto if presupuesto else False,
    }

    logger.info(
        "PR validada: id=%s valida=%s faltantes=%s monto_estimado=%.0f",
        solicitud_id, valida, faltantes, monto_estimado,
    )

    return {
        "centro_costo": sc.get("centro_costo", ""),
        "presupuesto_max": presupuesto,
        "categoria": sc.get("categoria", ""),
        "descripcion": sc.get("descripcion", ""),
        "items": items,
        "fecha_requerida": sc.get("fecha_requerida", ""),
        "responsable": sc.get("responsable", ""),
        "pr_validada": pr_validada,
        "events": [{
            "type": "pr_validada",
            "solicitud_id": solicitud_id,
            "valida": valida,
            "faltantes": faltantes,
            "monto_estimado": pr_validada["monto_estimado"],
        }],
    }


def buscar_proveedores(state: CompraState) -> dict:
    """Filtra el catálogo homologado por categoría."""
    categoria = state.get("categoria", "")
    suppliers = get_suppliers(get_data_dir())

    candidatos = [s for s in suppliers if categoria in s.get("categorias", [])]
    if not candidatos:
        # Fallback: todos los homologados — el comparador decidirá.
        candidatos = [s for s in suppliers if s.get("homologado", False)]

    logger.info("Proveedores candidatos: %d para categoría=%s", len(candidatos), categoria)

    return {
        "suppliers_candidatos": candidatos,
        "events": [{
            "type": "proveedores_buscados",
            "categoria": categoria,
            "total_candidatos": len(candidatos),
            "ids": [s.get("id") for s in candidatos],
        }],
    }


def lanzar_rfq(state: CompraState) -> dict:
    """Genera RFQs determinísticas para los candidatos seleccionados."""
    candidatos = state.get("suppliers_candidatos", [])
    items = state.get("items", [])
    fecha = _today_iso()

    rfqs: list = []
    for s in candidatos:
        rfq_id = f"RFQ-{state.get('solicitud_id', 'PR')}-{s.get('id', '')}"
        rfqs.append({
            "rfq_id": rfq_id,
            "supplier_id": s.get("id"),
            "supplier_nombre": s.get("nombre"),
            "fecha_emision": fecha,
            "items": items,
            "descripcion": state.get("descripcion", ""),
            "fecha_requerida": state.get("fecha_requerida", ""),
            "estado": "ENVIADA",
        })

    logger.info("RFQs emitidas: %d", len(rfqs))

    return {
        "rfqs_emitidas": rfqs,
        "events": [{
            "type": "rfqs_emitidas",
            "total": len(rfqs),
            "ids": [r["rfq_id"] for r in rfqs],
        }],
    }


def recopilar_cotizaciones(state: CompraState) -> dict:
    """Toma las cotizaciones del escenario (DEMO) o de los stubs por proveedor."""
    scenario_id = state.get("solicitud_id", "")
    sc = get_scenario(scenario_id, get_data_dir())
    cotizaciones_demo = sc.get("cotizaciones", [])

    rfqs = state.get("rfqs_emitidas", [])
    rfq_by_supplier = {r["supplier_id"]: r["rfq_id"] for r in rfqs}

    cotizaciones: list = []
    for c in cotizaciones_demo:
        sup_id = c.get("supplier_id")
        if sup_id not in rfq_by_supplier:
            continue
        cotizaciones.append({
            "rfq_id": rfq_by_supplier[sup_id],
            "supplier_id": sup_id,
            "precio_total": float(c.get("precio_total", 0) or 0),
            "plazo_dias": int(c.get("plazo_dias", 30) or 30),
            "moneda": c.get("moneda", "CLP"),
            "condiciones_pago": c.get("condiciones_pago", "30 días"),
            "validez_dias": int(c.get("validez_dias", 15) or 15),
            "incluye_iva": bool(c.get("incluye_iva", True)),
        })

    logger.info("Cotizaciones recibidas: %d de %d RFQs", len(cotizaciones), len(rfqs))

    return {
        "cotizaciones_recibidas": cotizaciones,
        "events": [{
            "type": "cotizaciones_recibidas",
            "total": len(cotizaciones),
            "esperadas": len(rfqs),
            "tasa_respuesta_pct": round(100.0 * len(cotizaciones) / max(len(rfqs), 1), 1),
        }],
    }


def comparar_ofertas(state: CompraState) -> dict:
    """Aplica score multi-criterio sobre cotizaciones y proveedores."""
    policy = get_policy(get_data_dir())
    weights = policy.get("score_weights", {"precio": 0.4, "plazo": 0.3, "riesgo": 0.3})
    cotizaciones = state.get("cotizaciones_recibidas", [])
    candidatos = {s["id"]: s for s in state.get("suppliers_candidatos", [])}
    presupuesto = float(state.get("presupuesto_max", 0) or 0)

    comparativa: list = []
    for c in cotizaciones:
        sup = candidatos.get(c["supplier_id"], {})
        scores = _score_quote(c, sup, weights, presupuesto)
        comparativa.append({
            "supplier_id": c["supplier_id"],
            "supplier_nombre": sup.get("nombre", c["supplier_id"]),
            "preferido": bool(sup.get("preferido", False)),
            "riesgo": float(sup.get("riesgo", 0.5) or 0.5),
            "precio_total": c["precio_total"],
            "plazo_dias": c["plazo_dias"],
            "condiciones_pago": c["condiciones_pago"],
            **scores,
        })

    comparativa.sort(key=lambda x: x["score_total"], reverse=True)

    logger.info(
        "Comparativa: %d ofertas evaluadas — mejor=%s score=%.1f",
        len(comparativa),
        comparativa[0]["supplier_id"] if comparativa else "n/a",
        comparativa[0]["score_total"] if comparativa else 0.0,
    )

    return {
        "comparativa": comparativa,
        "events": [{
            "type": "comparativa_lista",
            "total_ofertas": len(comparativa),
            "mejor_supplier": comparativa[0]["supplier_id"] if comparativa else None,
            "mejor_score": comparativa[0]["score_total"] if comparativa else 0.0,
        }],
    }


# ---------------------------------------------------------------------------
# Router de política de compras
# ---------------------------------------------------------------------------

def politica_compras_router(state: CompraState) -> str:
    """
    Decide si la compra puede aprobarse vía vía rápida o si requiere comité.
    Activa comité cuando:
      - Monto del mejor proveedor > umbral_comite
      - O el mejor proveedor NO está en la lista preferida y monto > umbral_no_preferido
      - O la PR llegó marcada como inválida
    """
    policy = get_policy(get_data_dir())
    umbral_comite = float(policy.get("umbral_comite_clp", 25_000_000) or 25_000_000)
    umbral_no_pref = float(policy.get("umbral_no_preferido_clp", 5_000_000) or 5_000_000)

    pr = state.get("pr_validada", {})
    comparativa = state.get("comparativa", [])

    if not pr.get("valida", False):
        return "requiere_comite"

    if not comparativa:
        return "requiere_comite"

    mejor = comparativa[0]
    monto = float(mejor.get("precio_total", 0) or 0)
    es_preferido = bool(mejor.get("preferido", False))

    if monto > umbral_comite:
        return "requiere_comite"
    if not es_preferido and monto > umbral_no_pref:
        return "requiere_comite"

    return "dentro_politica"


def escalar_comite(state: CompraState) -> dict:
    """Genera nota de escalación al comité de compras."""
    policy = get_policy(get_data_dir())
    comparativa = state.get("comparativa", [])
    mejor = comparativa[0] if comparativa else {}
    pr = state.get("pr_validada", {})

    razones: list = []
    if not pr.get("valida", False):
        razones.append(f"PR incompleta — faltan: {', '.join(pr.get('faltantes', []))}")
    monto = float(mejor.get("precio_total", 0) or 0)
    if monto > float(policy.get("umbral_comite_clp", 25_000_000)):
        razones.append(f"Monto {monto:,.0f} CLP supera umbral de comité ({policy.get('umbral_comite_clp'):,.0f})")
    if mejor and not mejor.get("preferido", False) and monto > float(policy.get("umbral_no_preferido_clp", 5_000_000)):
        razones.append(
            f"Mejor oferta proviene de proveedor NO preferido ({mejor.get('supplier_nombre')}) "
            f"y monto {monto:,.0f} supera umbral para no preferidos."
        )

    nota = (
        f"⚠️ ESCALACIÓN COMITÉ DE COMPRAS — {state.get('solicitud_id', '')}\n"
        f"Centro de costo: {state.get('centro_costo', '')}\n"
        f"Categoría: {state.get('categoria', '')}\n"
        f"Mejor oferta: {mejor.get('supplier_nombre', 'n/a')} · "
        f"{mejor.get('precio_total', 0):,.0f} CLP · {mejor.get('plazo_dias', 0)} días\n"
        f"Razones de escalación:\n" + "\n".join(f"  - {r}" for r in razones) + "\n"
        "Acción requerida: revisión por comité antes de la aprobación final."
    )

    escalacion = {
        "requerida": True,
        "razones": razones,
        "monto": monto,
        "supplier_recomendado": mejor.get("supplier_id"),
        "nota": nota,
    }

    logger.info("Escalación a comité: razones=%s", razones)

    return {
        "escalacion_comite": escalacion,
        "events": [{
            "type": "comite_escalado",
            "monto": monto,
            "razones": razones,
        }],
    }


def recomendar_proveedor(state: CompraState) -> dict:
    """Recomendación justificada (LLM opt-in) sobre el mejor proveedor."""
    comparativa = state.get("comparativa", [])
    if not comparativa:
        return {
            "recomendacion": {"recomendado": False, "razon": "Sin cotizaciones para evaluar."},
            "events": [{"type": "recomendacion_emitida", "recomendado": False}],
        }

    mejor = comparativa[0]
    runner_up = comparativa[1] if len(comparativa) >= 2 else None

    diff_pct = 0.0
    if runner_up and mejor["score_total"] > 0:
        diff_pct = round((mejor["score_total"] - runner_up["score_total"]) / mejor["score_total"] * 100, 1)

    fallback = (
        f"Se recomienda al proveedor {mejor['supplier_nombre']} (id={mejor['supplier_id']}) "
        f"con score total {mejor['score_total']}. "
        f"Precio: {mejor['precio_total']:,.0f} CLP · plazo {mejor['plazo_dias']} días. "
        f"Diferencia frente al segundo: {diff_pct}% en score total. "
        f"{'Proveedor preferido del catálogo.' if mejor.get('preferido') else 'Proveedor homologado fuera del listado preferido.'}"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres jefe de compras corporativo. Justifica en español (máx 80 palabras) "
            f"por qué se recomienda al proveedor {mejor['supplier_nombre']} "
            f"con precio {mejor['precio_total']:,.0f} CLP, plazo {mejor['plazo_dias']} días, "
            f"score {mejor['score_total']} (precio={mejor['score_precio']}, "
            f"plazo={mejor['score_plazo']}, riesgo={mejor['score_riesgo']}). "
            f"Es {'preferido' if mejor.get('preferido') else 'no preferido'}. "
            f"Cita el % de ventaja sobre el segundo: {diff_pct}%."
        )
        justificacion = _llm_invoke(prompt, fallback)
    else:
        justificacion = fallback

    rec = {
        "recomendado": True,
        "supplier_id": mejor["supplier_id"],
        "supplier_nombre": mejor["supplier_nombre"],
        "precio_total": mejor["precio_total"],
        "plazo_dias": mejor["plazo_dias"],
        "condiciones_pago": mejor["condiciones_pago"],
        "score_total": mejor["score_total"],
        "diferencia_pct_vs_segundo": diff_pct,
        "justificacion": justificacion,
        "preferido": mejor.get("preferido", False),
    }

    logger.info(
        "Recomendación emitida: %s score=%.1f diff=%.1f%%",
        mejor["supplier_id"], mejor["score_total"], diff_pct,
    )

    return {
        "recomendacion": rec,
        "events": [{
            "type": "recomendacion_emitida",
            "supplier_id": mejor["supplier_id"],
            "score": mejor["score_total"],
            "diferencia_pct": diff_pct,
        }],
    }


def aprobacion_responsable(state: CompraState) -> dict:
    """
    Simula aprobación digital del responsable del centro de costo.
    DEMO determinista: aprueba si la PR es válida, hay recomendación y monto ≤ presupuesto.
    Si hubo escalación a comité, marca aprobación como CONDICIONAL pendiente de comité.
    """
    pr = state.get("pr_validada", {})
    rec = state.get("recomendacion", {})
    escalacion = state.get("escalacion_comite", {})
    presupuesto = float(state.get("presupuesto_max", 0) or 0)
    monto = float(rec.get("precio_total", 0) or 0)

    if not rec.get("recomendado", False):
        estado = "RECHAZADA"
        motivo = "Sin recomendación válida del agente."
    elif not pr.get("valida", False):
        estado = "RECHAZADA"
        motivo = f"PR incompleta: {', '.join(pr.get('faltantes', []))}"
    elif presupuesto > 0 and monto > presupuesto:
        estado = "RECHAZADA"
        motivo = f"Monto {monto:,.0f} excede presupuesto autorizado ({presupuesto:,.0f})"
    elif escalacion.get("requerida", False):
        estado = "CONDICIONAL"
        motivo = "Aprobación condicionada a ratificación del comité de compras."
    else:
        estado = "APROBADA"
        motivo = "Aprobación automática — dentro de política y presupuesto."

    aprobacion = {
        "estado": estado,
        "motivo": motivo,
        "responsable": state.get("responsable", ""),
        "fecha": _today_iso(),
        "monto": monto,
    }

    logger.info("Aprobación: estado=%s monto=%.0f", estado, monto)

    return {
        "aprobacion": aprobacion,
        "events": [{
            "type": "aprobacion_emitida",
            "estado": estado,
            "monto": monto,
        }],
    }


def generar_orden_compra(state: CompraState) -> dict:
    """Emite la OC con trazabilidad SHA-256 si la aprobación lo permite."""
    aprob = state.get("aprobacion", {})
    rec = state.get("recomendacion", {})

    if aprob.get("estado") == "RECHAZADA" or not rec.get("recomendado", False):
        oc = {
            "emitida": False,
            "estado": aprob.get("estado", "RECHAZADA"),
            "motivo": aprob.get("motivo", ""),
        }
        logger.info("OC no emitida: estado=%s", oc["estado"])
        return {
            "orden_compra": oc,
            "events": [{"type": "oc_no_emitida", "estado": oc["estado"]}],
        }

    payload = {
        "po_numero": f"OC-{state.get('solicitud_id', '')}-{_today_iso().replace('-', '')}",
        "solicitud_id": state.get("solicitud_id", ""),
        "centro_costo": state.get("centro_costo", ""),
        "supplier_id": rec.get("supplier_id"),
        "supplier_nombre": rec.get("supplier_nombre"),
        "monto_total": rec.get("precio_total"),
        "plazo_dias": rec.get("plazo_dias"),
        "condiciones_pago": rec.get("condiciones_pago"),
        "items": state.get("items", []),
        "fecha_emision": _today_iso(),
        "estado_aprobacion": aprob.get("estado"),
    }
    payload["sha256"] = _po_hash(payload)

    oc = {
        "emitida": True,
        "estado": "EMITIDA" if aprob.get("estado") == "APROBADA" else "PENDIENTE_COMITE",
        **payload,
    }

    logger.info(
        "OC %s: numero=%s monto=%.0f hash=%s",
        oc["estado"], oc["po_numero"], oc.get("monto_total", 0), oc["sha256"],
    )

    return {
        "orden_compra": oc,
        "events": [{
            "type": "oc_emitida",
            "po_numero": oc["po_numero"],
            "monto": oc.get("monto_total"),
            "estado": oc["estado"],
            "hash": oc["sha256"],
        }],
    }


def producir_resumen(state: CompraState) -> dict:
    """Resumen ejecutivo para el comprador / aprobador."""
    rec = state.get("recomendacion", {})
    aprob = state.get("aprobacion", {})
    oc = state.get("orden_compra", {})
    escalacion = state.get("escalacion_comite", {})
    pr = state.get("pr_validada", {})

    estado_label = aprob.get("estado", "—")
    estado_icon = {"APROBADA": "🟢", "CONDICIONAL": "🟡", "RECHAZADA": "🔴"}.get(estado_label, "⚪")

    fallback = (
        f"## Resumen de adquisición — {state.get('solicitud_id', '')}\n\n"
        f"**Centro de costo:** {state.get('centro_costo', '—')} · "
        f"**Categoría:** {state.get('categoria', '—')}\n"
        f"**Estado de aprobación:** {estado_icon} {estado_label} — {aprob.get('motivo', '')}\n\n"
        f"### Decisión\n"
        f"- Proveedor recomendado: **{rec.get('supplier_nombre', '—')}** "
        f"({'preferido' if rec.get('preferido') else 'no preferido'})\n"
        f"- Monto total: **{rec.get('precio_total', 0):,.0f} CLP** · "
        f"Plazo: {rec.get('plazo_dias', '—')} días · "
        f"Pago: {rec.get('condiciones_pago', '—')}\n"
        f"- Score: {rec.get('score_total', 0)} · "
        f"Ventaja sobre segundo: {rec.get('diferencia_pct_vs_segundo', 0)}%\n\n"
        f"### Trazabilidad\n"
        f"- PR válida: {'sí' if pr.get('valida') else 'no'}"
        f"{' · faltantes: ' + ', '.join(pr.get('faltantes', [])) if pr.get('faltantes') else ''}\n"
        f"- Escalación comité: {'sí — ' + str(len(escalacion.get('razones', []))) + ' razones' if escalacion.get('requerida') else 'no'}\n"
        f"- OC emitida: {'sí · ' + oc.get('po_numero', '') + ' · hash=' + oc.get('sha256', '') if oc.get('emitida') else 'no'}\n\n"
        f"_Reporte generado por agente de compras — Caso 07. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres director de compras. Redacta un resumen ejecutivo en español (máx 200 palabras) "
            f"para el responsable del centro de costo {state.get('centro_costo', '')} sobre la "
            f"solicitud {state.get('solicitud_id', '')} categoría {state.get('categoria', '')}. "
            f"Recomendación: {rec.get('supplier_nombre', '')} por {rec.get('precio_total', 0):,.0f} CLP "
            f"en {rec.get('plazo_dias', 0)} días. Estado: {estado_label}. "
            f"Escalación a comité: {'sí' if escalacion.get('requerida') else 'no'}. "
            f"Sé directo, orientado a decisión, cierra con próximos pasos."
        )
        resumen = _llm_invoke(prompt, fallback)
    else:
        resumen = fallback

    logger.info(
        "Resumen generado: solicitud=%s estado=%s modo=%s",
        state.get("solicitud_id", ""), estado_label,
        "LIVE" if _LIVE_MODE else "DEMO",
    )

    return {
        "resumen": resumen,
        "done": True,
        "events": [{
            "type": "compra_completada",
            "solicitud_id": state.get("solicitud_id", ""),
            "estado_aprobacion": estado_label,
            "oc_emitida": bool(oc.get("emitida", False)),
        }],
    }


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def compile_graph():
    builder = StateGraph(CompraState)

    builder.add_node("validar_solicitud", validar_solicitud)
    builder.add_node("buscar_proveedores", buscar_proveedores)
    builder.add_node("lanzar_rfq", lanzar_rfq)
    builder.add_node("recopilar_cotizaciones", recopilar_cotizaciones)
    builder.add_node("comparar_ofertas", comparar_ofertas)
    builder.add_node("escalar_comite", escalar_comite)
    builder.add_node("recomendar_proveedor", recomendar_proveedor)
    builder.add_node("aprobacion_responsable", aprobacion_responsable)
    builder.add_node("generar_orden_compra", generar_orden_compra)
    builder.add_node("producir_resumen", producir_resumen)

    builder.set_entry_point("validar_solicitud")
    builder.add_edge("validar_solicitud", "buscar_proveedores")
    builder.add_edge("buscar_proveedores", "lanzar_rfq")
    builder.add_edge("lanzar_rfq", "recopilar_cotizaciones")
    builder.add_edge("recopilar_cotizaciones", "comparar_ofertas")

    builder.add_conditional_edges(
        "comparar_ofertas",
        politica_compras_router,
        {
            "dentro_politica": "recomendar_proveedor",
            "requiere_comite": "escalar_comite",
        },
    )
    builder.add_edge("escalar_comite", "recomendar_proveedor")
    builder.add_edge("recomendar_proveedor", "aprobacion_responsable")
    builder.add_edge("aprobacion_responsable", "generar_orden_compra")
    builder.add_edge("generar_orden_compra", "producir_resumen")
    builder.add_edge("producir_resumen", END)

    return builder.compile(checkpointer=MemorySaver())
