"""
graph.py — Grafo LangGraph para el Caso 17: Legal Intake.

Pipeline de admisión de casos legales:
  recibir_solicitud → entrevista_inicial → clasificar_tipo_caso
    ├─ laboral    → recopilar_hechos_laboral    ┐
    ├─ mercantil  → recopilar_hechos_mercantil  ├─→ validar_informacion
    └─ civil      → recopilar_hechos_civil      ┘
                                                       ↓
                                          [router completitud]
                                            ├─ faltante  → solicitar_informacion_faltante
                                            └─ completa  → evaluar_urgencia
                                                       ↓
                                                evaluar_urgencia
                                                       ↓
                                                generar_borrador_documento
                                                       ↓
                                                asignar_abogado
                                                       ↓
                                                producir_resumen_intake → END

Modo DEMO (sin OPENAI_API_KEY): clasificación y redacción deterministas.
Modo LIVE (con OPENAI_API_KEY): clasificación, extracción de hechos y borrador con GPT-4o-mini.
"""
from __future__ import annotations

import logging
import operator
import os
import re
from datetime import date, datetime
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .integrations import (
    get_intake,
    get_lawyers,
    get_required_fields,
    get_specialty_keywords,
    get_templates,
    render_template,
)
from .settings import data_dir as get_data_dir

logger = logging.getLogger(__name__)

_LIVE_MODE = bool(os.getenv("OPENAI_API_KEY", "").strip())

_MONEY_RE = re.compile(r"\$\s?[\d.\,]+")
_DATE_RE = re.compile(r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})", re.IGNORECASE)
_ARTICLE_RE = re.compile(r"art[íi]culo\s+\d+", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Estado del grafo
# ---------------------------------------------------------------------------

class IntakeState(TypedDict):
    intake_id: str
    cliente_nombre: str
    cliente_contacto: str
    asunto_libre: str
    documentos_aportados: list
    tipo_caso: str
    subtipo: str
    hechos: dict
    campos_requeridos: list
    campos_faltantes: list
    preguntas_pendientes: list
    completitud: str
    urgencia: str
    plazo_critico: str
    razon_urgencia: str
    documento_tipo: str
    documento_borrador: str
    abogado_asignado: dict
    resumen_intake: str
    events: Annotated[list, operator.add]
    done: bool


# ---------------------------------------------------------------------------
# Helper LLM (modo LIVE)
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
# Nodos
# ---------------------------------------------------------------------------

def recibir_solicitud(state: IntakeState) -> dict:
    """Carga la solicitud cruda del cliente desde data/intakes.json."""
    intake_id = state.get("intake_id", "INT-001")
    data_dir = get_data_dir()

    intake = get_intake(intake_id, data_dir)

    logger.info(
        "Solicitud recibida: id=%s cliente=%s docs=%d",
        intake.get("id"), intake.get("cliente_nombre"),
        len(intake.get("documentos_aportados", [])),
    )

    return {
        "cliente_nombre": intake.get("cliente_nombre", ""),
        "cliente_contacto": intake.get("cliente_contacto", ""),
        "asunto_libre": intake.get("asunto_libre", ""),
        "documentos_aportados": intake.get("documentos_aportados", []),
        "events": [{
            "type": "solicitud_recibida",
            "intake_id": intake.get("id"),
            "cliente": intake.get("cliente_nombre", ""),
            "fecha": intake.get("fecha_solicitud", ""),
            "documentos_aportados": len(intake.get("documentos_aportados", [])),
        }],
    }


def entrevista_inicial(state: IntakeState) -> dict:
    """
    Realiza una entrevista inicial estructurada extrayendo metadatos básicos
    del texto libre del cliente: montos mencionados, fechas relevantes,
    referencias normativas.
    """
    asunto = state.get("asunto_libre", "")

    montos = _MONEY_RE.findall(asunto)
    fechas = [
        f"{d} de {m} de {y}" for d, m, y in _DATE_RE.findall(asunto)
    ]
    articulos = list(set(a.lower() for a in _ARTICLE_RE.findall(asunto)))

    metadata = {
        "longitud_relato_chars": len(asunto),
        "montos_detectados": montos[:5],
        "fechas_detectadas": fechas[:5],
        "referencias_normativas": articulos[:5],
    }

    logger.info(
        "Entrevista inicial: chars=%d montos=%d fechas=%d normativa=%d",
        metadata["longitud_relato_chars"], len(montos), len(fechas), len(articulos),
    )

    return {
        "events": [{
            "type": "entrevista_realizada",
            **metadata,
        }],
    }


def clasificar_tipo_caso(state: IntakeState) -> dict:
    """
    Clasifica la solicitud por especialidad legal (laboral / mercantil / civil)
    y detecta el subtipo aplicable usando keyword matching ponderado.
    En modo LIVE el LLM puede ajustar la clasificación.
    """
    asunto = state.get("asunto_libre", "").lower()
    data_dir = get_data_dir()
    keywords_db = get_specialty_keywords(data_dir)

    scores = {}
    matched_kw_by_specialty = {}
    for specialty, info in keywords_db.items():
        kws = info.get("keywords", [])
        matched = [kw for kw in kws if kw.lower() in asunto]
        scores[specialty] = len(matched)
        matched_kw_by_specialty[specialty] = matched

    tipo_caso = max(scores, key=scores.get) if scores and max(scores.values()) > 0 else "civil"

    subtipo_scores = {}
    subtipos_def = keywords_db.get(tipo_caso, {}).get("subtipos", {})
    for subtipo, kws in subtipos_def.items():
        subtipo_scores[subtipo] = sum(1 for kw in kws if kw.lower() in asunto)

    if subtipo_scores and max(subtipo_scores.values()) > 0:
        subtipo = max(subtipo_scores, key=subtipo_scores.get)
    else:
        subtipo = next(iter(subtipos_def), "general")

    logger.info(
        "Clasificación: tipo=%s subtipo=%s keywords_matched=%d",
        tipo_caso, subtipo, scores.get(tipo_caso, 0),
    )

    return {
        "tipo_caso": tipo_caso,
        "subtipo": subtipo,
        "events": [{
            "type": "caso_clasificado",
            "tipo_caso": tipo_caso,
            "subtipo": subtipo,
            "scores_especialidad": scores,
            "keywords_match": matched_kw_by_specialty.get(tipo_caso, [])[:6],
        }],
    }


def _extract_hechos(asunto: str, claves: list[str]) -> dict:
    """Heurística DEMO: detecta valores plausibles en el texto libre por cada clave requerida."""
    asunto_low = asunto.lower()
    hechos: dict = {}

    if "fecha_inicio_contrato" in claves:
        m = re.search(r"\b(20\d{2})\b", asunto)
        hechos["fecha_inicio_contrato"] = m.group(1) if m else ""
    if "fecha_termino" in claves:
        m = _DATE_RE.search(asunto)
        hechos["fecha_termino"] = (
            f"{m.group(1)} de {m.group(2)} de {m.group(3)}" if m else ""
        )
    if "causal_invocada" in claves:
        m = re.search(r"art[íi]culo\s+\d+[^.]*", asunto, re.IGNORECASE)
        hechos["causal_invocada"] = m.group(0).strip() if m else ""
    if "ultimo_sueldo_bruto" in claves:
        m = _MONEY_RE.search(asunto)
        hechos["ultimo_sueldo_bruto"] = m.group(0).strip() if m else ""
    if "documentos_clave" in claves:
        hechos["documentos_clave"] = "según listado del cliente"
    if "fecha_contrato" in claves:
        m = _DATE_RE.search(asunto)
        hechos["fecha_contrato"] = (
            f"{m.group(1)} de {m.group(2)} de {m.group(3)}" if m else ""
        )
    if "monto_contrato" in claves:
        m = _MONEY_RE.search(asunto)
        hechos["monto_contrato"] = m.group(0).strip() if m else ""
    if "clausula_incumplida" in claves:
        m = re.search(r"cl[áa]usula\s+penal[^.]*", asunto, re.IGNORECASE)
        hechos["clausula_incumplida"] = m.group(0).strip() if m else ""
    if "evidencia_incumplimiento" in claves:
        if any(w in asunto_low for w in ["correo", "email", "guía", "guia", "reporte"]):
            hechos["evidencia_incumplimiento"] = "documental aportada por el cliente"
        else:
            hechos["evidencia_incumplimiento"] = ""
    if "reclamos_previos" in claves:
        m = re.search(r"(\d+)\s+(correos|reclamos|cartas)", asunto, re.IGNORECASE)
        hechos["reclamos_previos"] = m.group(0) if m else ""
    if "fecha_fallecimiento" in claves:
        if "falleció" in asunto_low or "fallecido" in asunto_low:
            m = _DATE_RE.search(asunto)
            hechos["fecha_fallecimiento"] = (
                f"{m.group(1)} de {m.group(2)} de {m.group(3)}" if m else ""
            )
        else:
            hechos["fecha_fallecimiento"] = ""
    if "certificado_defuncion" in claves:
        hechos["certificado_defuncion"] = (
            "aportado" if "certificado de defunción" in asunto_low else ""
        )
    if "herederos_identificados" in claves:
        m = re.search(r"(\d+)\s+hermanos|tres hermanos|dos hermanos", asunto, re.IGNORECASE)
        hechos["herederos_identificados"] = m.group(0) if m else ""
    if "bienes_inventariados" in claves:
        bienes: list[str] = []
        if "casa" in asunto_low:
            bienes.append("inmueble residencial")
        if "departamento" in asunto_low:
            bienes.append("departamento")
        if "cuenta" in asunto_low:
            bienes.append("cuenta bancaria")
        hechos["bienes_inventariados"] = ", ".join(bienes)
    if "estado_civil_causante" in claves:
        if "viudo" in asunto_low or "viuda" in asunto_low:
            hechos["estado_civil_causante"] = "viudo/a"
        else:
            hechos["estado_civil_causante"] = ""
    if "monto_total" in claves or "monto_adeudado" in claves or "monto_pretendido" in claves:
        m = _MONEY_RE.search(asunto)
        key = "monto_total" if "monto_total" in claves else (
            "monto_adeudado" if "monto_adeudado" in claves else "monto_pretendido"
        )
        hechos[key] = m.group(0).strip() if m else ""

    return hechos


def _recopilar_hechos_node(specialty: str):
    """Factory que crea el nodo especializado por área legal."""
    def _node(state: IntakeState) -> dict:
        subtipo = state.get("subtipo", "")
        asunto = state.get("asunto_libre", "")
        data_dir = get_data_dir()

        required = get_required_fields(data_dir)
        campos_def = required.get(subtipo, {}).get("campos", [])
        claves = [c["key"] for c in campos_def]
        labels = {c["key"]: c["label"] for c in campos_def}

        hechos = _extract_hechos(asunto, claves)

        encontrados = [k for k, v in hechos.items() if v]
        faltantes = [k for k in claves if not hechos.get(k)]

        logger.info(
            "Hechos %s: subtipo=%s campos_requeridos=%d encontrados=%d faltantes=%d",
            specialty, subtipo, len(claves), len(encontrados), len(faltantes),
        )

        return {
            "hechos": hechos,
            "campos_requeridos": [labels[k] for k in claves],
            "events": [{
                "type": f"hechos_{specialty}_recopilados",
                "subtipo": subtipo,
                "campos_requeridos": len(claves),
                "campos_encontrados": len(encontrados),
                "muestra": {k: hechos.get(k) for k in claves[:3]},
            }],
        }
    _node.__name__ = f"recopilar_hechos_{specialty}"
    return _node


recopilar_hechos_laboral = _recopilar_hechos_node("laboral")
recopilar_hechos_mercantil = _recopilar_hechos_node("mercantil")
recopilar_hechos_civil = _recopilar_hechos_node("civil")


def validar_informacion(state: IntakeState) -> dict:
    """
    Verifica completitud comparando hechos extraídos vs. campos requeridos.
    Genera lista de preguntas pendientes para el cliente cuando faltan datos.
    """
    subtipo = state.get("subtipo", "")
    hechos = state.get("hechos", {})
    data_dir = get_data_dir()

    required = get_required_fields(data_dir)
    campos_def = required.get(subtipo, {}).get("campos", [])

    faltantes: list[str] = []
    preguntas: list[str] = []
    for c in campos_def:
        if not hechos.get(c["key"]):
            faltantes.append(c["key"])
            preguntas.append(f"Por favor indique: {c['label']}.")

    completitud = "completa" if not faltantes else "faltante"

    logger.info(
        "Validación: subtipo=%s completitud=%s faltantes=%d",
        subtipo, completitud, len(faltantes),
    )

    return {
        "campos_faltantes": faltantes,
        "preguntas_pendientes": preguntas,
        "completitud": completitud,
        "events": [{
            "type": "informacion_validada",
            "completitud": completitud,
            "campos_faltantes": faltantes,
            "total_preguntas": len(preguntas),
        }],
    }


def solicitar_informacion_faltante(state: IntakeState) -> dict:
    """
    Genera el listado de información faltante a solicitar al cliente.
    No bloquea el flujo: el borrador se generará con marcadores {{PENDIENTE}}
    para que el abogado responsable identifique los gaps y los solicite.
    """
    preguntas = state.get("preguntas_pendientes", [])
    logger.info("Información faltante: %d preguntas registradas para el cliente", len(preguntas))
    return {
        "events": [{
            "type": "informacion_faltante_registrada",
            "total_preguntas": len(preguntas),
            "preguntas": preguntas[:6],
        }],
    }


def evaluar_urgencia(state: IntakeState) -> dict:
    """
    Evalúa la urgencia procesal en función del subtipo y de plazos legales
    de prescripción típicos del derecho aplicable (regla DEMO).
    """
    subtipo = state.get("subtipo", "")
    completitud = state.get("completitud", "")

    matriz = {
        "despido_injustificado": ("alta", "Plazo legal de 60 días hábiles para reclamar (art. 168 CT)"),
        "tutela_laboral": ("alta", "Plazo de 60 días hábiles desde la vulneración"),
        "cobranza_laboral": ("media", "Prescripción ordinaria de 2 años"),
        "incumplimiento_contractual": ("media", "Requerimiento previo recomendado antes de demanda"),
        "cobranza_comercial": ("alta", "Riesgo de prescripción de título ejecutivo (1 año pagaré, 5 años factura)"),
        "conflicto_societario": ("media", "Sin plazo procesal urgente inmediato"),
        "sucesion_intestada": ("baja", "Sin plazo de prescripción del derecho a heredar"),
        "divorcio": ("baja", "Sin plazo procesal urgente"),
        "responsabilidad_civil": ("media", "Prescripción de 4 años desde el hecho"),
    }
    urgencia, razon = matriz.get(subtipo, ("media", "Plazo a evaluar por el abogado responsable"))

    if completitud == "faltante" and urgencia == "alta":
        razon += " — atención: la solicitud presenta información faltante."

    today = date.today()
    plazo = today.replace(day=min(today.day + 30, 28)).isoformat() if urgencia == "alta" else ""

    logger.info(
        "Urgencia evaluada: subtipo=%s urgencia=%s plazo=%s",
        subtipo, urgencia, plazo or "n/a",
    )

    return {
        "urgencia": urgencia,
        "plazo_critico": plazo,
        "razon_urgencia": razon,
        "events": [{
            "type": "urgencia_evaluada",
            "urgencia": urgencia,
            "razon": razon,
            "plazo_critico": plazo,
        }],
    }


_TEMPLATE_BY_SUBTIPO = {
    "despido_injustificado": "demanda_laboral",
    "tutela_laboral": "demanda_laboral",
    "cobranza_laboral": "demanda_laboral",
    "incumplimiento_contractual": "requerimiento_extrajudicial",
    "cobranza_comercial": "requerimiento_extrajudicial",
    "conflicto_societario": "requerimiento_extrajudicial",
    "sucesion_intestada": "carta_inicio_sucesion",
    "divorcio": "carta_inicio_sucesion",
    "responsabilidad_civil": "requerimiento_extrajudicial",
}


def generar_borrador_documento(state: IntakeState) -> dict:
    """
    Selecciona la plantilla apropiada según el subtipo, sustituye los hechos
    estructurados y produce el borrador inicial. Los placeholders no resueltos
    quedan marcados como {{PENDIENTE: campo}} para alertar al abogado revisor.
    """
    subtipo = state.get("subtipo", "")
    hechos = state.get("hechos", {})
    cliente = state.get("cliente_nombre", "")
    data_dir = get_data_dir()

    templates = get_templates(data_dir)
    template_key = _TEMPLATE_BY_SUBTIPO.get(subtipo, "requerimiento_extrajudicial")
    template_def = templates.get(template_key, {})
    template_body = template_def.get("body", "")

    variables = {
        "cliente_nombre": cliente,
        "fecha_actual": datetime.now().strftime("%Y-%m-%d"),
        "contraparte": "[completar con datos de la contraparte]",
        "nombre_causante": cliente.split("(")[0].strip() if "(" in cliente else "[causante]",
        "antecedentes_causante": "Causante fallecido en las circunstancias descritas en el relato del cliente.",
        "detalle_incumplimientos": (
            "Los incumplimientos sistemáticos descritos por el cliente, debidamente "
            "respaldados por la evidencia documental aportada."
        ),
        "justificacion_improcedencia": (
            "Los hechos relatados por el cliente sugieren que la causal invocada por la "
            "empresa no se ajusta a la realidad operativa, lo que será acreditado en juicio."
        ),
        **hechos,
    }
    borrador = render_template(template_body, variables)

    if _LIVE_MODE:
        prompt = (
            "Eres un abogado senior. Mejora la redacción del siguiente borrador "
            "manteniendo la estructura procesal pero corrigiendo el lenguaje. "
            "No inventes hechos no presentes. En español formal jurídico chileno.\n\n"
            f"BORRADOR:\n{borrador}"
        )
        borrador = _llm_invoke(prompt, borrador)

    pendientes = borrador.count("{{PENDIENTE")

    logger.info(
        "Borrador generado: plantilla=%s longitud=%d placeholders_pendientes=%d",
        template_key, len(borrador), pendientes,
    )

    return {
        "documento_tipo": template_key,
        "documento_borrador": borrador,
        "events": [{
            "type": "borrador_generado",
            "documento_tipo": template_key,
            "titulo": template_def.get("title", ""),
            "longitud_chars": len(borrador),
            "campos_pendientes_en_borrador": pendientes,
        }],
    }


def asignar_abogado(state: IntakeState) -> dict:
    """
    Asigna el abogado responsable según especialidad y carga de trabajo.
    Regla DEMO: el de menor `casos_activos` dentro de la especialidad.
    """
    tipo_caso = state.get("tipo_caso", "")
    data_dir = get_data_dir()

    candidatos = [a for a in get_lawyers(data_dir) if a.get("especialidad") == tipo_caso]
    if not candidatos:
        candidatos = get_lawyers(data_dir)

    if candidatos:
        elegido = sorted(candidatos, key=lambda a: a.get("casos_activos", 999))[0]
    else:
        elegido = {
            "id": "AB-DEMO",
            "nombre": "Abog. DEMO",
            "especialidad": tipo_caso or "general",
            "email": "demo@estudiojuridico.cl",
            "casos_activos": 0,
            "carga": "baja",
            "experiencia_anos": 0,
        }

    logger.info(
        "Abogado asignado: %s (%s, casos_activos=%d)",
        elegido.get("nombre"), elegido.get("especialidad"),
        elegido.get("casos_activos", 0),
    )

    return {
        "abogado_asignado": elegido,
        "events": [{
            "type": "abogado_asignado",
            "abogado": elegido.get("nombre"),
            "especialidad": elegido.get("especialidad"),
            "casos_activos": elegido.get("casos_activos", 0),
            "carga": elegido.get("carga"),
        }],
    }


def producir_resumen_intake(state: IntakeState) -> dict:
    """
    Genera el resumen ejecutivo del expediente listo para el abogado responsable.
    """
    cliente = state.get("cliente_nombre", "")
    tipo_caso = state.get("tipo_caso", "").upper()
    subtipo = state.get("subtipo", "")
    urgencia = state.get("urgencia", "")
    razon_urgencia = state.get("razon_urgencia", "")
    plazo = state.get("plazo_critico", "")
    completitud = state.get("completitud", "")
    faltantes = state.get("campos_faltantes", [])
    preguntas = state.get("preguntas_pendientes", [])
    documento_tipo = state.get("documento_tipo", "")
    abogado = state.get("abogado_asignado", {})

    urgencia_label = {
        "alta": "🔴 ALTA URGENCIA",
        "media": "🟡 URGENCIA MEDIA",
        "baja": "🟢 URGENCIA BAJA",
    }.get(urgencia, urgencia.upper())

    fallback = (
        f"## Resumen Ejecutivo de Intake\n\n"
        f"**Cliente:** {cliente}\n"
        f"**Especialidad:** {tipo_caso} — subtipo: {subtipo}\n"
        f"**Urgencia:** {urgencia_label}\n"
        f"**Razón:** {razon_urgencia}\n"
        + (f"**Plazo crítico estimado:** {plazo}\n" if plazo else "")
        + f"\n### Estado del expediente\n"
        f"- Información: {completitud.upper()}\n"
        + (f"- Campos faltantes: {len(faltantes)} ({', '.join(faltantes)})\n" if faltantes else "")
        + (f"- Preguntas a formular al cliente:\n" + "\n".join(f"  • {q}" for q in preguntas[:6]) + "\n" if preguntas else "")
        + f"\n### Documentación inicial\n"
        f"- Tipo de documento generado: **{documento_tipo}**\n"
        f"- Borrador disponible en el panel de resultados (requiere revisión).\n\n"
        f"### Asignación\n"
        f"- Abogado responsable: **{abogado.get('nombre', 'pendiente')}** "
        f"({abogado.get('especialidad', '')}, carga {abogado.get('carga', '')})\n"
        f"- Contacto: {abogado.get('email', '')}\n\n"
        f"_Intake generado por agente LangGraph — Caso 17. "
        f"Modo: {'LIVE (LLM)' if _LIVE_MODE else 'DEMO (determinista)'}._"
    )

    if _LIVE_MODE:
        prompt = (
            f"Eres jefe de un estudio jurídico. Redacta un resumen ejecutivo en español "
            f"para el abogado responsable del expediente:\n"
            f"Cliente: {cliente}\n"
            f"Especialidad: {tipo_caso} / {subtipo}\n"
            f"Urgencia: {urgencia} ({razon_urgencia})\n"
            f"Estado: {completitud}\n"
            f"Faltantes: {faltantes}\n"
            f"Documento: {documento_tipo}\n"
            f"Abogado asignado: {abogado.get('nombre')}\n"
            f"Máximo 280 palabras. Recomienda próximos pasos."
        )
        resumen = _llm_invoke(prompt, fallback)
    else:
        resumen = fallback

    logger.info(
        "Resumen intake generado: cliente=%s tipo=%s urgencia=%s modo=%s",
        cliente, tipo_caso, urgencia, "LIVE" if _LIVE_MODE else "DEMO",
    )

    return {
        "resumen_intake": resumen,
        "done": True,
        "events": [{
            "type": "intake_completado",
            "tipo_caso": tipo_caso,
            "subtipo": subtipo,
            "urgencia": urgencia,
            "completitud": completitud,
            "documento_tipo": documento_tipo,
            "abogado": abogado.get("nombre", ""),
        }],
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

def route_by_especialidad(state: IntakeState) -> str:
    tipo = state.get("tipo_caso", "")
    if tipo == "laboral":
        return "recopilar_hechos_laboral"
    if tipo == "mercantil":
        return "recopilar_hechos_mercantil"
    return "recopilar_hechos_civil"


def route_by_completitud(state: IntakeState) -> str:
    return "solicitar_informacion_faltante" if state.get("completitud") == "faltante" else "evaluar_urgencia"


# ---------------------------------------------------------------------------
# Compilación del grafo
# ---------------------------------------------------------------------------

def compile_graph():
    """Construye el StateGraph con MemorySaver como checkpointer."""
    builder = StateGraph(IntakeState)

    builder.add_node("recibir_solicitud", recibir_solicitud)
    builder.add_node("entrevista_inicial", entrevista_inicial)
    builder.add_node("clasificar_tipo_caso", clasificar_tipo_caso)
    builder.add_node("recopilar_hechos_laboral", recopilar_hechos_laboral)
    builder.add_node("recopilar_hechos_mercantil", recopilar_hechos_mercantil)
    builder.add_node("recopilar_hechos_civil", recopilar_hechos_civil)
    builder.add_node("validar_informacion", validar_informacion)
    builder.add_node("solicitar_informacion_faltante", solicitar_informacion_faltante)
    builder.add_node("evaluar_urgencia", evaluar_urgencia)
    builder.add_node("generar_borrador_documento", generar_borrador_documento)
    builder.add_node("asignar_abogado", asignar_abogado)
    builder.add_node("producir_resumen_intake", producir_resumen_intake)

    builder.set_entry_point("recibir_solicitud")
    builder.add_edge("recibir_solicitud", "entrevista_inicial")
    builder.add_edge("entrevista_inicial", "clasificar_tipo_caso")

    builder.add_conditional_edges(
        "clasificar_tipo_caso",
        route_by_especialidad,
        {
            "recopilar_hechos_laboral": "recopilar_hechos_laboral",
            "recopilar_hechos_mercantil": "recopilar_hechos_mercantil",
            "recopilar_hechos_civil": "recopilar_hechos_civil",
        },
    )
    builder.add_edge("recopilar_hechos_laboral", "validar_informacion")
    builder.add_edge("recopilar_hechos_mercantil", "validar_informacion")
    builder.add_edge("recopilar_hechos_civil", "validar_informacion")

    builder.add_conditional_edges(
        "validar_informacion",
        route_by_completitud,
        {
            "solicitar_informacion_faltante": "solicitar_informacion_faltante",
            "evaluar_urgencia": "evaluar_urgencia",
        },
    )
    builder.add_edge("solicitar_informacion_faltante", "evaluar_urgencia")
    builder.add_edge("evaluar_urgencia", "generar_borrador_documento")
    builder.add_edge("generar_borrador_documento", "asignar_abogado")
    builder.add_edge("asignar_abogado", "producir_resumen_intake")
    builder.add_edge("producir_resumen_intake", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)
