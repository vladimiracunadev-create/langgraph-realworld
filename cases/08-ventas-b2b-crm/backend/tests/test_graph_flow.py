"""Tests del grafo LangGraph — Caso 08: Ventas B2B + CRM."""
from src.graph import (
    B2BSalesState,
    calificar_lead,
    compile_graph,
    investigar_cuenta,
    route_by_icp,
    route_by_senal,
)


def _base_state(account_id: str = "ACC-001") -> B2BSalesState:
    return {
        "account_id": account_id,
        "company_name": "", "industria": "", "industria_tag": "",
        "tamano_empresa": "", "pais": "", "web": "",
        "contacto_principal": {}, "enriquecimiento": {},
        "icp_score": 0, "icp_nivel": "", "icp_razones": [], "califica": False,
        "mensaje_outreach": {}, "canal": "", "cadencia": [],
        "envio": {}, "respuesta_prospect": {}, "senal_interes": "",
        "siguiente_accion": "", "crm_record": {}, "resumen_comercial": "",
        "events": [], "done": False,
    }


def test_graph_compiles():
    assert compile_graph() is not None


def test_investigar_cuenta_acc001():
    out = investigar_cuenta(_base_state("ACC-001"))
    assert out["company_name"]
    assert out["industria_tag"] == "logistics"
    assert out["enriquecimiento"]["headcount"] == 850
    assert out["events"][0]["type"] == "cuenta_investigada"


def test_calificar_lead_alto():
    state = _base_state()
    state["industria_tag"] = "logistics"
    state["tamano_empresa"] = "mid-market"
    state["enriquecimiento"] = {
        "headcount": 850, "tecnologias": ["Salesforce", "AWS"],
        "señales_compra": ["RFP abierto"], "noticias_recientes": ["Expansión"],
        "pain_points_publicos": [],
    }
    out = calificar_lead(state)
    assert out["califica"] is True
    assert out["icp_score"] >= 70
    assert out["icp_nivel"] == "alto"


def test_calificar_lead_descarta_pequena():
    state = _base_state()
    state["industria_tag"] = "retail_traditional"
    state["tamano_empresa"] = "small"
    state["enriquecimiento"] = {
        "headcount": 50, "tecnologias": ["Excel"],
        "señales_compra": [], "noticias_recientes": [],
        "pain_points_publicos": [],
    }
    out = calificar_lead(state)
    assert out["califica"] is False
    assert out["icp_nivel"] == "fuera_icp"


def test_route_by_icp_califica():
    s = _base_state(); s["califica"] = True
    assert route_by_icp(s) == "personalizar_outreach"


def test_route_by_icp_no_califica():
    s = _base_state(); s["califica"] = False
    assert route_by_icp(s) == "descartar_y_registrar"


def test_route_by_senal_positivo():
    s = _base_state(); s["senal_interes"] = "positivo"
    assert route_by_senal(s) == "escalar_ejecutivo"


def test_route_by_senal_negativo():
    s = _base_state(); s["senal_interes"] = "negativo"
    assert route_by_senal(s) == "descartar_y_registrar"


def test_route_by_senal_sin_respuesta():
    s = _base_state(); s["senal_interes"] = "sin_respuesta"
    assert route_by_senal(s) == "programar_followup"


# ---------------------------------------------------------------------------
# Flujos end-to-end para las 4 cuentas DEMO
# ---------------------------------------------------------------------------

def test_e2e_acc001_meeting_scheduled():
    """ACC-001 (NorthPeak Logistics) → ICP alto + respuesta positiva → Meeting Scheduled."""
    g = compile_graph()
    out = g.invoke(_base_state("ACC-001"), config={"configurable": {"thread_id": "t-acc001"}})
    assert out["done"] is True
    assert out["califica"] is True
    assert out["icp_nivel"] == "alto"
    assert out["senal_interes"] == "positivo"
    assert out["crm_record"]["deal_stage"] == "Meeting Scheduled"
    assert out["crm_record"]["ae_assigned"]["industrias"]


def test_e2e_acc002_nurturing():
    """ACC-002 (Synthwave) → ICP medio + sin respuesta → Nurturing."""
    g = compile_graph()
    out = g.invoke(_base_state("ACC-002"), config={"configurable": {"thread_id": "t-acc002"}})
    assert out["done"] is True
    assert out["califica"] is True
    assert out["senal_interes"] == "sin_respuesta"
    assert out["crm_record"]["deal_stage"] == "Nurturing"
    assert "fecha_proximo_toque" in str(out.get("siguiente_accion", "")).lower() or "follow" in out["siguiente_accion"].lower()


def test_e2e_acc003_disqualified():
    """ACC-003 (Andina Comercializadora) → fuera_icp → Disqualified sin enviar mail."""
    g = compile_graph()
    out = g.invoke(_base_state("ACC-003"), config={"configurable": {"thread_id": "t-acc003"}})
    assert out["done"] is True
    assert out["califica"] is False
    assert out["icp_nivel"] == "fuera_icp"
    assert out["crm_record"]["deal_stage"] == "Disqualified"
    # No debe haber enviado outreach
    assert not out.get("mensaje_outreach", {}).get("cuerpo")


def test_e2e_acc004_closed_lost():
    """ACC-004 (FinSecure Bank) → ICP medio + respuesta negativa → Closed Lost."""
    g = compile_graph()
    out = g.invoke(_base_state("ACC-004"), config={"configurable": {"thread_id": "t-acc004"}})
    assert out["done"] is True
    assert out["califica"] is True
    assert out["senal_interes"] == "negativo"
    assert out["crm_record"]["deal_stage"] == "Closed Lost"


def test_e2e_eventos_completos():
    """ACC-001 debe producir todos los eventos clave del pipeline feliz."""
    g = compile_graph()
    out = g.invoke(_base_state("ACC-001"), config={"configurable": {"thread_id": "t-events"}})
    types = [e["type"] for e in out["events"]]
    for expected in [
        "cuenta_investigada", "lead_calificado",
        "outreach_personalizado", "canal_seleccionado",
        "envio_simulado", "respuesta_monitoreada",
        "ejecutivo_escalado", "crm_actualizado", "resumen_generado",
    ]:
        assert expected in types, f"falta evento {expected} en {types}"
