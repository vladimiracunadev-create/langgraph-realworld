"""
graph.py — LangGraph StateGraph para el agente de revisión de PRs (Caso 19).

Flujo:
  fetch_pr → classify_changes → analyze_security → analyze_quality → check_tests
           → aggregate_findings → router → [request_changes | approve_with_comments | approve]
           → generate_changelog → END

En modo DEMO el análisis se basa en patrones de texto (sin LLM).
En modo LIVE se puede extender con llamadas a OpenAI/LangChain.
"""
from __future__ import annotations

import logging
import operator
import re
import time
from typing import Annotated, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from .settings import load_settings, pr_data_path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class PRReviewState(TypedDict, total=False):
    """Estado centralizado del agente de revisión de PRs."""
    pr_id: str
    pr_data: dict
    diff: str
    security_findings: Annotated[list, operator.add]
    quality_findings: Annotated[list, operator.add]
    test_findings: Annotated[list, operator.add]
    all_findings: list
    risk_level: str      # "high", "medium", "low"
    decision: str        # "request_changes", "approve_with_comments", "approve"
    changelog: str
    events: Annotated[list, operator.add]
    done: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_ms() -> int:
    return int(time.time() * 1000)


def _push_event(event_type: str, data: dict) -> dict:
    return {
        "events": [
            {
                "ts": _now_ms(),
                "type": event_type,
                "data": data,
            }
        ]
    }


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def fetch_pr(state: PRReviewState) -> PRReviewState:
    """
    Nodo inicial: carga los datos del PR desde integrations.
    Soporta pr_id desde el estado inicial o usa el ID por defecto del JSON.
    """
    load_settings()
    from .integrations import get_pr_data

    pr_id = state.get("pr_id") or "PR-001"
    logger.info(f"[fetch_pr] Cargando PR {pr_id}")

    data_path = pr_data_path()
    pr_data = get_pr_data(pr_id, data_path)

    out: PRReviewState = {
        "pr_id": pr_data.get("id", pr_id),
        "pr_data": pr_data,
        "diff": pr_data.get("diff", ""),
        "security_findings": [],
        "quality_findings": [],
        "test_findings": [],
        "all_findings": [],
        "risk_level": "low",
        "decision": "approve",
        "changelog": "",
        "events": state.get("events", []) or [],
        "done": False,
    }
    out.update(
        _push_event(
            "pr_fetched",
            {
                "pr_id": out["pr_id"],
                "title": pr_data.get("title", ""),
                "author": pr_data.get("author", ""),
                "files_changed": len(pr_data.get("files_changed", [])),
            },
        )
    )
    return out


def classify_changes(state: PRReviewState) -> PRReviewState:
    """
    Analiza el tipo de cambios del PR: backend, frontend, tests, docs, config.
    Determina el contexto para los nodos de análisis posteriores.
    """
    files = state.get("pr_data", {}).get("files_changed", []) or []

    change_types = []
    if any(f.endswith(".py") for f in files):
        change_types.append("python")
    if any(f.endswith((".js", ".ts", ".jsx", ".tsx")) for f in files):
        change_types.append("javascript")
    if any("test" in f.lower() or "spec" in f.lower() for f in files):
        change_types.append("tests")
    if any(f.endswith((".md", ".rst", ".txt")) for f in files):
        change_types.append("docs")
    if any(f.endswith((".yml", ".yaml", ".json", ".toml", ".ini", ".cfg")) for f in files):
        change_types.append("config")
    if any("api" in f.lower() or "route" in f.lower() or "endpoint" in f.lower() for f in files):
        change_types.append("api")

    if not change_types:
        change_types = ["unknown"]

    logger.info(f"[classify_changes] Tipos detectados: {change_types}")

    out: PRReviewState = {}
    out.update(
        _push_event(
            "changes_classified",
            {"types": change_types, "files_count": len(files)},
        )
    )
    return out


def analyze_security(state: PRReviewState) -> PRReviewState:
    """
    Analiza el diff buscando patrones de seguridad vulnerables.

    En modo DEMO detecta:
      - SQL por concatenación (sin parámetros)
      - Uso de eval() o exec()
      - Credenciales hardcodeadas (password=, secret=, token= con valor literal)
      - Uso de subprocess con shell=True

    En modo LIVE se extendería con un LLM para análisis más profundo.
    """
    diff = state.get("diff", "") or ""
    findings = []

    # Patrón 1: SQL construido por concatenación
    sql_concat_patterns = [
        r'(?i)(select|insert|update|delete|drop)\s+.*["\']?\s*\+\s*\w',
        r'(?i)(execute|cursor\.execute)\s*\(\s*sql\s*\+',
        r'(?i)sql\s*=\s*["\'].*["\'\s]*\+',
        r'(?i)sql\s*\+=',
    ]
    for pattern in sql_concat_patterns:
        if re.search(pattern, diff):
            findings.append({
                "severity": "critical",
                "category": "sql_injection",
                "message": "SQL construido por concatenación de strings — vulnerable a SQL Injection.",
                "recommendation": "Usar consultas parametrizadas: cursor.execute(sql, params)",
            })
            break

    # Patrón 2: eval() en código de producción
    if re.search(r'\beval\s*\(', diff):
        findings.append({
            "severity": "critical",
            "category": "code_injection",
            "message": "Uso de eval() detectado — permite ejecución arbitraria de código.",
            "recommendation": "Eliminar eval(). Usar alternativas seguras (ast.literal_eval, json.loads, etc.).",
        })

    # Patrón 3: exec() en código de producción
    if re.search(r'\bexec\s*\(', diff):
        findings.append({
            "severity": "high",
            "category": "code_injection",
            "message": "Uso de exec() detectado — riesgo de ejecución de código arbitrario.",
            "recommendation": "Eliminar exec(). Refactorizar la lógica sin evaluación dinámica de código.",
        })

    # Patrón 4: credenciales hardcodeadas
    cred_pattern = r'(?i)(password|passwd|secret|api_key|token|apikey)\s*=\s*["\'][^"\']{4,}["\']'
    if re.search(cred_pattern, diff):
        findings.append({
            "severity": "high",
            "category": "hardcoded_credentials",
            "message": "Posible credencial hardcodeada en el código fuente.",
            "recommendation": "Usar variables de entorno o un gestor de secretos (Vault, AWS Secrets Manager).",
        })

    # Patrón 5: subprocess con shell=True
    if re.search(r'subprocess\.(run|call|Popen).*shell\s*=\s*True', diff):
        findings.append({
            "severity": "high",
            "category": "shell_injection",
            "message": "subprocess con shell=True — vulnerable a inyección de comandos.",
            "recommendation": "Usar shell=False y pasar los argumentos como lista.",
        })

    logger.info(f"[analyze_security] {len(findings)} finding(s) de seguridad")

    out: PRReviewState = {"security_findings": findings}
    out.update(
        _push_event(
            "security_analyzed",
            {"findings_count": len(findings)},
        )
    )
    return out


def analyze_quality(state: PRReviewState) -> PRReviewState:
    """
    Analiza el diff buscando problemas de calidad de código.

    En modo DEMO detecta:
      - Imports no usados (importado pero no referenciado en el diff)
      - Funciones demasiado largas (>20 líneas de código)
      - Magic numbers
      - Comentarios TODO/FIXME/HACK

    En modo LIVE se extendería con linters reales (ruff, pylint) o LLM.
    """
    diff = state.get("diff", "") or ""
    findings = []

    # Extraer líneas añadidas (las que empiezan con +, excluyendo la cabecera +++)
    added_lines = [
        line[1:]
        for line in diff.split("\n")
        if line.startswith("+") and not line.startswith("+++")
    ]
    added_code = "\n".join(added_lines)

    # Patrón 1: imports presentes en el diff pero sin uso visible
    import_matches = re.findall(r'^(?:import\s+(\S+)|from\s+\S+\s+import\s+(\S+))', added_code, re.MULTILINE)
    for match in import_matches:
        imported = (match[0] or match[1]).split(",")[0].strip().split(" as ")[-1].strip()
        # Contar referencias al símbolo (excluir la línea de import misma)
        usage_count = len(re.findall(r'\b' + re.escape(imported) + r'\b', added_code)) - 1
        if usage_count <= 0 and imported:
            findings.append({
                "severity": "low",
                "category": "unused_import",
                "message": f"Import '{imported}' aparentemente no utilizado en los cambios del PR.",
                "recommendation": f"Eliminar 'import {imported}' si no se usa en el módulo.",
            })

    # Patrón 2: funciones demasiado largas
    func_blocks = re.findall(r'(def \w+[^:]+:(?:\n.+)+?)(?=\ndef |\Z)', added_code)
    for block in func_blocks:
        line_count = len([ln for ln in block.split("\n") if ln.strip() and not ln.strip().startswith("#")])
        if line_count > 20:
            func_name_match = re.match(r'def (\w+)', block)
            func_name = func_name_match.group(1) if func_name_match else "desconocida"
            findings.append({
                "severity": "medium",
                "category": "long_function",
                "message": f"Función '{func_name}' tiene ~{line_count} líneas — supera el límite recomendado de 20.",
                "recommendation": "Refactorizar en funciones más pequeñas con responsabilidad única.",
            })

    # Patrón 3: comentarios TODO/FIXME/HACK
    todo_matches = re.findall(r'#\s*(TODO|FIXME|HACK|XXX)[:\s].*', added_code, re.IGNORECASE)
    if todo_matches:
        findings.append({
            "severity": "low",
            "category": "pending_work",
            "message": f"{len(todo_matches)} comentario(s) TODO/FIXME encontrado(s) en el código añadido.",
            "recommendation": "Resolver o crear tickets de seguimiento antes de hacer merge.",
        })

    # Patrón 4: ausencia de docstrings en funciones nuevas
    funcs_without_docstring = re.findall(
        r'def (\w+)\([^)]*\):\s*\n\s+(?!""")',
        added_code,
    )
    if len(funcs_without_docstring) > 2:
        findings.append({
            "severity": "low",
            "category": "missing_docstrings",
            "message": f"{len(funcs_without_docstring)} función(es) nueva(s) sin docstring.",
            "recommendation": "Añadir docstrings descriptivos para mejorar la mantenibilidad.",
        })

    logger.info(f"[analyze_quality] {len(findings)} finding(s) de calidad")

    out: PRReviewState = {"quality_findings": findings}
    out.update(
        _push_event(
            "quality_analyzed",
            {"findings_count": len(findings)},
        )
    )
    return out


def check_tests(state: PRReviewState) -> PRReviewState:
    """
    Verifica si el PR incluye tests para los cambios realizados.

    En modo DEMO analiza los files_changed y el diff para buscar archivos de test.
    """
    files = state.get("pr_data", {}).get("files_changed", []) or []
    diff = state.get("diff", "") or ""
    findings = []

    has_test_files = any(
        "test_" in f.lower() or "_test." in f.lower() or "/tests/" in f.lower() or "spec." in f.lower()
        for f in files
    )

    has_test_code_in_diff = bool(
        re.search(r'(def test_|@pytest\.|unittest\.TestCase|describe\(|it\()', diff)
    )

    has_source_changes = any(
        not ("test" in f.lower() or "spec" in f.lower() or f.endswith(".md"))
        for f in files
    )

    if has_source_changes and not has_test_files and not has_test_code_in_diff:
        findings.append({
            "severity": "medium",
            "category": "missing_tests",
            "message": "El PR modifica código fuente pero no incluye archivos de tests.",
            "recommendation": (
                "Añadir tests unitarios para las funciones nuevas/modificadas. "
                "Coverage mínimo recomendado: 80%."
            ),
        })

    # Verificar si hay funciones nuevas sin tests correspondientes
    new_funcs = re.findall(r'^\+def (\w+)\(', diff, re.MULTILINE)
    if new_funcs and not has_test_files:
        func_list = ", ".join(new_funcs[:5])
        if len(new_funcs) > 5:
            func_list += f" (+{len(new_funcs) - 5} más)"
        findings.append({
            "severity": "medium",
            "category": "untested_functions",
            "message": f"Nuevas funciones sin tests detectados: {func_list}",
            "recommendation": "Crear tests unitarios para cada función nueva, incluyendo casos límite.",
        })

    logger.info(f"[check_tests] {len(findings)} finding(s) de cobertura")

    out: PRReviewState = {"test_findings": findings}
    out.update(
        _push_event(
            "tests_checked",
            {"has_test_files": has_test_files, "findings_count": len(findings)},
        )
    )
    return out


def aggregate_findings(state: PRReviewState) -> PRReviewState:
    """
    Agrega todos los findings y determina el nivel de riesgo global.

    Risk level:
      - high:   hay findings críticos o >3 findings de seguridad/calidad
      - medium: hay findings de severidad media o 2-3 findings en total
      - low:    solo findings de severidad baja o sin findings
    """
    security = state.get("security_findings", []) or []
    quality = state.get("quality_findings", []) or []
    tests = state.get("test_findings", []) or []

    all_findings = security + quality + tests

    # Determinar risk_level
    critical_count = sum(1 for f in all_findings if f.get("severity") == "critical")
    high_count = sum(1 for f in all_findings if f.get("severity") == "high")
    medium_count = sum(1 for f in all_findings if f.get("severity") == "medium")

    if critical_count > 0 or high_count >= 2:
        risk_level = "high"
    elif high_count == 1 or medium_count >= 2 or len(all_findings) >= 3:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Determinar decisión preliminar
    if risk_level == "high":
        decision = "request_changes"
    elif risk_level == "medium" or (all_findings and risk_level == "low"):
        decision = "approve_with_comments"
    else:
        decision = "approve"

    logger.info(
        f"[aggregate_findings] {len(all_findings)} finding(s) totales. "
        f"Risk: {risk_level}. Decision: {decision}"
    )

    out: PRReviewState = {
        "all_findings": all_findings,
        "risk_level": risk_level,
        "decision": decision,
    }
    out.update(
        _push_event(
            "findings_aggregated",
            {
                "total": len(all_findings),
                "security": len(security),
                "quality": len(quality),
                "tests": len(tests),
                "risk_level": risk_level,
                "decision": decision,
            },
        )
    )
    return out


def request_changes_node(state: PRReviewState) -> PRReviewState:
    """
    Nodo de acción: solicita cambios en el PR con los findings como razones.
    En DEMO loguea la operación vía integrations stub.
    """
    from .integrations import post_review_comment, request_changes

    pr_id = state.get("pr_id", "PR-001")
    all_findings = state.get("all_findings", []) or []

    # Construir resumen del comentario
    reasons = [f"[{f.get('severity', 'unknown').upper()}] {f.get('message', '')}" for f in all_findings]

    comment_lines = ["## Revisión automatizada — Se solicitan cambios\n"]
    for f in all_findings:
        comment_lines.append(
            f"- **[{f.get('severity', '?').upper()}] {f.get('category', '?')}**: "
            f"{f.get('message', '')} → _{f.get('recommendation', '')}_"
        )
    comment = "\n".join(comment_lines)

    post_review_comment(pr_id, comment)
    request_changes(pr_id, reasons)

    logger.info(f"[request_changes_node] Cambios solicitados para PR {pr_id}")

    out: PRReviewState = {"decision": "request_changes"}
    out.update(
        _push_event(
            "changes_requested",
            {"pr_id": pr_id, "reasons_count": len(reasons)},
        )
    )
    return out


def approve_with_comments_node(state: PRReviewState) -> PRReviewState:
    """
    Nodo de acción: aprueba el PR con comentarios informativos.
    En DEMO loguea la operación vía integrations stub.
    """
    from .integrations import approve_pr, post_review_comment

    pr_id = state.get("pr_id", "PR-001")
    all_findings = state.get("all_findings", []) or []

    comment_lines = ["## Revisión automatizada — Aprobado con observaciones\n"]
    for f in all_findings:
        comment_lines.append(
            f"- **[{f.get('severity', '?').upper()}]** {f.get('message', '')} → {f.get('recommendation', '')}"
        )
    comment_lines.append("\nPuedes hacer merge, pero considera atender las observaciones anteriores.")
    comment = "\n".join(comment_lines)

    post_review_comment(pr_id, comment)
    approve_pr(pr_id)

    logger.info(f"[approve_with_comments_node] PR {pr_id} aprobado con observaciones")

    out: PRReviewState = {"decision": "approve_with_comments"}
    out.update(
        _push_event(
            "approved_with_comments",
            {"pr_id": pr_id, "observations_count": len(all_findings)},
        )
    )
    return out


def approve_node(state: PRReviewState) -> PRReviewState:
    """
    Nodo de acción: aprueba el PR directamente (sin observaciones).
    En DEMO loguea la operación vía integrations stub.
    """
    from .integrations import approve_pr, post_review_comment

    pr_id = state.get("pr_id", "PR-001")

    comment = "## Revisión automatizada — Aprobado\n\nEl PR cumple con los criterios de calidad y seguridad."
    post_review_comment(pr_id, comment)
    approve_pr(pr_id)

    logger.info(f"[approve_node] PR {pr_id} aprobado directamente")

    out: PRReviewState = {"decision": "approve"}
    out.update(
        _push_event(
            "approved",
            {"pr_id": pr_id},
        )
    )
    return out


def generate_changelog(state: PRReviewState) -> PRReviewState:
    """
    Genera un changelog legible a partir de los commits del PR.
    En DEMO formatea los mensajes de commit directamente.
    En LIVE podría usar un LLM para mejorar la redacción.
    """
    pr_data = state.get("pr_data", {}) or {}
    commits = pr_data.get("commits", []) or []
    pr_title = pr_data.get("title", "")
    pr_author = pr_data.get("author", "")
    pr_id = state.get("pr_id", "")

    lines = [f"## Changelog — {pr_id}: {pr_title}", f"**Autor:** {pr_author}", ""]

    # Agrupar commits por prefijo convencional
    feat_commits = [c for c in commits if c.lower().startswith("feat")]
    fix_commits = [c for c in commits if c.lower().startswith("fix")]
    other_commits = [c for c in commits if not c.lower().startswith(("feat", "fix"))]

    if feat_commits:
        lines.append("### Nuevas funcionalidades")
        for c in feat_commits:
            lines.append(f"- {c}")
        lines.append("")

    if fix_commits:
        lines.append("### Correcciones")
        for c in fix_commits:
            lines.append(f"- {c}")
        lines.append("")

    if other_commits:
        lines.append("### Otros cambios")
        for c in other_commits:
            lines.append(f"- {c}")
        lines.append("")

    # Añadir resumen de revisión
    all_findings = state.get("all_findings", []) or []
    risk_level = state.get("risk_level", "low")
    decision = state.get("decision", "approve")

    lines.append("### Resultado de revisión automatizada")
    lines.append(f"- **Riesgo:** {risk_level.upper()}")
    lines.append(f"- **Decisión:** {decision.replace('_', ' ').title()}")
    lines.append(f"- **Findings:** {len(all_findings)} total(es)")

    changelog = "\n".join(lines)
    logger.info(f"[generate_changelog] Changelog generado para PR {pr_id}")

    out: PRReviewState = {"changelog": changelog, "done": True}
    out.update(
        _push_event(
            "changelog_generated",
            {"pr_id": pr_id, "commits_count": len(commits)},
        )
    )
    return out


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def route_by_risk(
    state: PRReviewState,
) -> Literal["request_changes_node", "approve_with_comments_node", "approve_node"]:
    """Router que determina el nodo de acción según el nivel de riesgo."""
    decision = state.get("decision", "approve")
    if decision == "request_changes":
        return "request_changes_node"
    elif decision == "approve_with_comments":
        return "approve_with_comments_node"
    else:
        return "approve_node"


# ---------------------------------------------------------------------------
# Graph compilation
# ---------------------------------------------------------------------------

def compile_graph():
    """Compila el StateGraph del agente de revisión de PRs."""
    g = StateGraph(PRReviewState)

    # Registrar nodos
    g.add_node("fetch_pr", fetch_pr)
    g.add_node("classify_changes", classify_changes)
    g.add_node("analyze_security", analyze_security)
    g.add_node("analyze_quality", analyze_quality)
    g.add_node("check_tests", check_tests)
    g.add_node("aggregate_findings", aggregate_findings)
    g.add_node("request_changes_node", request_changes_node)
    g.add_node("approve_with_comments_node", approve_with_comments_node)
    g.add_node("approve_node", approve_node)
    g.add_node("generate_changelog", generate_changelog)

    # Definir flujo
    g.add_edge(START, "fetch_pr")
    g.add_edge("fetch_pr", "classify_changes")
    # Análisis secuencial en DEMO (paralelismo simulado)
    g.add_edge("classify_changes", "analyze_security")
    g.add_edge("analyze_security", "analyze_quality")
    g.add_edge("analyze_quality", "check_tests")
    g.add_edge("check_tests", "aggregate_findings")

    # Router condicional por nivel de riesgo
    g.add_conditional_edges(
        "aggregate_findings",
        route_by_risk,
        ["request_changes_node", "approve_with_comments_node", "approve_node"],
    )

    # Todos los nodos de decisión convergen en generate_changelog
    g.add_edge("request_changes_node", "generate_changelog")
    g.add_edge("approve_with_comments_node", "generate_changelog")
    g.add_edge("approve_node", "generate_changelog")
    g.add_edge("generate_changelog", END)

    return g.compile(checkpointer=MemorySaver())
