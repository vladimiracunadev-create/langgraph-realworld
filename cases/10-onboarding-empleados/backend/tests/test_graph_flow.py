"""Tests unitarios del grafo de onboarding - Caso 10."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def merge_state(state, delta):
    for key, value in delta.items():
        if key == "events":
            state[key] = (state.get(key) or []) + value
        else:
            state[key] = value


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

    merge_state(state, classify_role(state))
    assert state.get("role_type") in {"dev_backend", "dev_frontend", "sales", "ops", "mgmt"}

    merge_state(state, provision_tools(state))
    assert isinstance(state.get("tools_provisioned"), list)

    merge_state(state, create_corporate_accounts(state))
    accounts = state.get("accounts") or []
    assert len(accounts) >= 1

    merge_state(state, assign_permissions(state))
    assert isinstance(state.get("permissions"), list)

    merge_state(state, generate_checklist(state))
    checklist = state.get("checklist") or []
    assert len(checklist) >= 1

    merge_state(state, send_welcome_package(state))
    notifs = state.get("notifications") or []
    assert len(notifs) >= 1

    merge_state(state, confirm_onboarding(state))
    assert state.get("done") is True

    events = state.get("events") or []
    event_types = [event.get("type") for event in events]
    assert "loaded" in event_types
    assert "classified" in event_types
    assert "completed" in event_types


def test_classify_role_fallback():
    """Un rol desconocido debe caer a 'ops' (degradacion graciosa)."""
    from src.graph import classify_role

    state = {"employee": {"role": "alien_role", "name": "Test"}, "events": []}
    out = classify_role(state)
    assert out["role_type"] == "ops"


def test_checklist_has_period_labels():
    """El checklist estatico debe incluir etiquetas de periodo."""
    from src.graph import classify_role, generate_checklist, load_employee

    state = load_employee({"events": []})
    merge_state(state, classify_role(state))
    merge_state(state, generate_checklist(state))

    checklist = state.get("checklist") or []
    assert len(checklist) > 0
    labeled = [item for item in checklist if item.startswith("[")]
    assert len(labeled) > 0
