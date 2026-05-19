"""
test_graph_flow.py — Tests unitarios para el StateGraph del caso 19.

Verifica que el grafo compila y que los nodos de análisis producen
los resultados esperados en modo DEMO (basado en patrones de texto).
"""


def test_graph_compiles():
    """El grafo debe compilar sin lanzar ninguna excepción."""
    from src.graph import compile_graph
    graph = compile_graph()
    assert graph is not None


def test_graph_has_nodes():
    """El grafo compilado debe tener todos los nodos esperados."""
    from src.graph import compile_graph
    graph = compile_graph()
    # Verificar que el grafo es un objeto válido con get_graph
    g = graph.get_graph()
    node_names = set(g.nodes.keys())
    expected_nodes = {
        "fetch_pr",
        "classify_changes",
        "analyze_security",
        "analyze_quality",
        "check_tests",
        "aggregate_findings",
        "request_changes_node",
        "approve_with_comments_node",
        "approve_node",
        "generate_changelog",
    }
    for node in expected_nodes:
        assert node in node_names, f"Nodo '{node}' no encontrado en el grafo"


def test_security_analysis_detects_sql_injection():
    """
    analyze_security debe detectar SQL construido por concatenación
    cuando el diff contiene el patrón vulnerable.
    """
    from src.graph import analyze_security

    state = {
        "diff": (
            "diff --git a/app.py b/app.py\n"
            "+def search_users(query):\n"
            "+    sql = \"SELECT * FROM users WHERE name='\" + query + \"'\"\n"
            "+    cursor.execute(sql + input('more?'))\n"
            "+    return cursor.fetchall()\n"
        ),
        "pr_data": {"files_changed": ["app.py"]},
    }
    result = analyze_security(state)
    security_findings = result.get("security_findings", [])
    assert len(security_findings) > 0, "Debe detectar al menos un finding de seguridad"
    categories = [f.get("category") for f in security_findings]
    assert "sql_injection" in categories, f"Debe detectar sql_injection. Categorías encontradas: {categories}"


def test_security_analysis_detects_eval():
    """analyze_security debe detectar uso de eval()."""
    from src.graph import analyze_security

    state = {
        "diff": (
            "diff --git a/utils.py b/utils.py\n"
            "+def execute_command(cmd):\n"
            "+    result = eval(cmd)\n"
            "+    return result\n"
        ),
        "pr_data": {"files_changed": ["utils.py"]},
    }
    result = analyze_security(state)
    security_findings = result.get("security_findings", [])
    assert len(security_findings) > 0
    categories = [f.get("category") for f in security_findings]
    assert "code_injection" in categories


def test_security_analysis_clean_diff():
    """analyze_security no debe generar findings en un diff limpio."""
    from src.graph import analyze_security

    state = {
        "diff": (
            "diff --git a/utils.py b/utils.py\n"
            "+def add(a, b):\n"
            "+    \"\"\"Suma dos números.\"\"\"\n"
            "+    return a + b\n"
        ),
        "pr_data": {"files_changed": ["utils.py"]},
    }
    result = analyze_security(state)
    security_findings = result.get("security_findings", [])
    assert len(security_findings) == 0, f"No debe haber findings en diff limpio: {security_findings}"


def test_check_tests_detects_missing():
    """check_tests debe detectar que no hay tests cuando el PR no los incluye."""
    from src.graph import check_tests

    state = {
        "pr_data": {
            "files_changed": ["app/api/users.py", "app/utils/helpers.py"],
        },
        "diff": (
            "+def new_function():\n"
            "+    return 42\n"
        ),
    }
    result = check_tests(state)
    test_findings = result.get("test_findings", [])
    assert len(test_findings) > 0, "Debe detectar falta de tests"
    categories = [f.get("category") for f in test_findings]
    assert any(c in ("missing_tests", "untested_functions") for c in categories)


def test_check_tests_passes_with_test_files():
    """check_tests no debe generar findings cuando el PR incluye archivos de test."""
    from src.graph import check_tests

    state = {
        "pr_data": {
            "files_changed": ["app/api/users.py", "tests/test_users.py"],
        },
        "diff": (
            "+def new_function():\n"
            "+    return 42\n"
            "+def test_new_function():\n"
            "+    assert new_function() == 42\n"
        ),
    }
    result = check_tests(state)
    test_findings = result.get("test_findings", [])
    assert len(test_findings) == 0, f"No debe haber findings cuando hay tests: {test_findings}"


def test_aggregate_findings_high_risk():
    """aggregate_findings debe determinar risk_level 'high' con findings críticos."""
    from src.graph import aggregate_findings

    state = {
        "security_findings": [
            {"severity": "critical", "category": "sql_injection", "message": "SQL injection"},
            {"severity": "critical", "category": "code_injection", "message": "eval() usado"},
        ],
        "quality_findings": [],
        "test_findings": [],
    }
    result = aggregate_findings(state)
    assert result.get("risk_level") == "high"
    assert result.get("decision") == "request_changes"


def test_aggregate_findings_low_risk():
    """aggregate_findings debe determinar risk_level 'low' sin findings."""
    from src.graph import aggregate_findings

    state = {
        "security_findings": [],
        "quality_findings": [],
        "test_findings": [],
    }
    result = aggregate_findings(state)
    assert result.get("risk_level") == "low"
    assert result.get("decision") == "approve"


def test_full_graph_run():
    """
    Ejecuta el grafo completo en modo DEMO con el PR de muestra.
    Verifica que el estado final tiene los campos esperados.
    """

    from src.graph import compile_graph

    graph = compile_graph()
    cfg = {"configurable": {"thread_id": "test-full-run"}, "recursion_limit": 50}
    initial_state = {"pr_id": "PR-001", "events": []}
    out = graph.invoke(initial_state, config=cfg)

    assert isinstance(out, dict)
    assert out.get("done") is True
    assert out.get("decision") in ("request_changes", "approve_with_comments", "approve")
    assert out.get("risk_level") in ("high", "medium", "low")
    assert isinstance(out.get("all_findings"), list)
    assert isinstance(out.get("changelog"), str)
    assert len(out.get("changelog", "")) > 0
    assert isinstance(out.get("events"), list)
    assert len(out.get("events", [])) > 0
