"""Tests unitarios del grafo de onboarding – Caso 10."""
import sys
from pathlib import Path

# Asegura que 'src' sea importable desde el directorio de tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_full_onboarding_flow():
    from src.graph import (
        assign_permissions,
        classify_role,
        confirm_onboarding,
        create_corporate_accounts,
        generate_checklist,
        load_employee,
        provision_tools,
        send_welcome_package,
    )

    state = load_employee({"events": []})
    assert state.get("employee"), "Debe cargar el empleado"
    assert state.get("roles_config"), "Debe cargar la config de roles"

    state.update(classify_role(state))
    assert state.get("role_type") in {"dev_backend", "dev_frontend", "sales", "ops", "mgmt"}

    state.update(provision_tools(state))
    assert isinstance(state.get("tools_provisioned"), list)

    state.update(create_corporate_accounts(state))
    accounts = state.get("accounts") or []
    assert len(accounts) >= 1

    state.update(assign_permissions(state))
    assert isinstance(state.get("permissions"), list)

    state.update(generate_checklist(state))
    checklist = state.get("checklist") or []
    assert len(checklist) >= 1

    state.update(send_welcome_package(state))
    notifs = state.get("notifications") or []
    assert len(notifs) >= 1

    state.update(confirm_onboarding(state))
    assert state.get("done") is True

    events = state.get("events") or []
    event_types = [e.get("type") for e in events]
    assert "loaded" in event_types
    assert "classified" in event_types
    assert "completed" in event_types


def test_classify_role_fallback():
    """Un rol desconocido debe caer a 'ops' (degradación graciosa)."""
    from src.graph import classify_role

    state = {"employee": {"role": "alien_role", "name": "Test"}, "events": []}
    out = classify_role(state)
    assert out["role_type"] == "ops"


def test_checklist_has_period_labels():
    """El checklist estático debe incluir etiquetas de período."""
    from src.graph import classify_role, generate_checklist, load_employee

    state = load_employee({"events": []})
    state.update(classify_role(state))
    state.update(generate_checklist(state))

    checklist = state.get("checklist") or []
    assert len(checklist) > 0
    # Al menos uno debe tener formato "[Semana X] ..."
    labeled = [item for item in checklist if item.startswith("[")]
    assert len(labeled) > 0
