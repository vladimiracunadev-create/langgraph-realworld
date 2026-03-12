import re
import sqlite3
import unicodedata
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from .settings import settings

DEFAULT_LIMIT = 100
FORBIDDEN_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|attach|detach|pragma|replace|create|truncate)\b",
    re.IGNORECASE,
)
SELECT_SQL = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)

EXAMPLE_QUESTIONS = [
    "Cual es el producto mas caro?",
    "Ventas por ciudad",
    "Mejores clientes",
    "Recaudacion total",
    "Ultimas ventas",
]


class State(TypedDict, total=False):
    question: str
    sql_query: str
    execution_results: str
    chart_data: dict[str, Any]
    final_answer: str
    error: str
    row_count: int
    columns: list[str]
    mode: str


DB_SCHEMA = """
Tables:
1. products (id, name, category, price)
2. customers (id, name, city, email)
3. sales (id, product_id, customer_id, quantity, sale_date, total_amount)
"""

IS_DEMO_MODE = not settings.OPENAI_API_KEY

if not IS_DEMO_MODE:
    llm = ChatOpenAI(model="gpt-4o", api_key=settings.OPENAI_API_KEY, timeout=10)
else:
    llm = None


def normalize_question(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def demo_query_for(question: str) -> str | None:
    q = normalize_question(question)
    if "reciente" in q or "ultimas ventas" in q:
        return "SELECT s.sale_date, p.name, c.city, s.total_amount FROM sales s JOIN products p ON s.product_id = p.id JOIN customers c ON s.customer_id = c.id ORDER BY s.sale_date DESC LIMIT 5"
    if "caro" in q or "mayor precio" in q:
        return "SELECT name, price FROM products ORDER BY price DESC LIMIT 1"
    if "barato" in q or "menor precio" in q:
        return "SELECT name, price FROM products ORDER BY price ASC LIMIT 1"
    if "vendido" in q or "mas ventas" in q or "mayor venta" in q:
        return "SELECT p.name, SUM(s.quantity) AS total FROM sales s JOIN products p ON s.product_id = p.id GROUP BY p.id, p.name ORDER BY total DESC LIMIT 5"
    if "menos vendido" in q or "peor producto" in q:
        return "SELECT p.name, SUM(s.quantity) AS total FROM sales s JOIN products p ON s.product_id = p.id GROUP BY p.id, p.name ORDER BY total ASC LIMIT 5"
    if "ciudad" in q or "por ciudad" in q:
        return "SELECT c.city, SUM(s.total_amount) AS total FROM sales s JOIN customers c ON s.customer_id = c.id GROUP BY c.city ORDER BY total DESC"
    if "recaudacion" in q or "ingreso" in q or "ventas totales" in q or "monto total" in q:
        return "SELECT SUM(total_amount) AS gran_total FROM sales"
    if "promedio" in q:
        return "SELECT AVG(total_amount) AS promedio FROM sales"
    if "categoria" in q or "mejor categoria" in q:
        return "SELECT p.category, SUM(s.total_amount) AS total FROM sales s JOIN products p ON s.product_id = p.id GROUP BY p.category ORDER BY total DESC"
    if "mejores clientes" in q or ("cliente" in q and "gasto" in q) or "quien gasto mas" in q:
        return "SELECT c.name, SUM(s.total_amount) AS total FROM sales s JOIN customers c ON s.customer_id = c.id GROUP BY c.id, c.name ORDER BY total DESC LIMIT 5"
    if "cliente" in q:
        return "SELECT name, city, email FROM customers LIMIT 10"
    if "producto" in q:
        return "SELECT name, category, price FROM products LIMIT 10"
    return None


def sanitize_sql(query: str) -> str:
    clean = query.strip().replace("```sql", "").replace("```", "").strip()
    clean = clean[:-1] if clean.endswith(";") else clean

    if not SELECT_SQL.match(clean):
        raise ValueError("Only SELECT/CTE queries are allowed in Case 13.")
    if FORBIDDEN_SQL.search(clean):
        raise ValueError("Unsafe SQL detected.")
    if ";" in clean:
        raise ValueError("Multiple SQL statements are not allowed.")
    if " limit " not in clean.lower() and re.match(r"^\s*select\b", clean, re.IGNORECASE):
        clean = f"{clean} LIMIT {DEFAULT_LIMIT}"
    return clean


def choose_chart_type(labels: list[str], dataset_count: int) -> str:
    if dataset_count > 1:
        return "bar"
    if len(labels) <= 5:
        return "doughnut"
    if len(labels) <= 12:
        return "bar"
    return "line"


def build_chart_data(rows: list[sqlite3.Row], columns: list[str]) -> dict[str, Any]:
    if not rows or len(columns) < 2:
        return {}

    sample_row = dict(rows[0])
    numeric_columns = [
        col for col in columns[1:] if isinstance(sample_row.get(col), (int, float))
    ]
    if not numeric_columns:
        return {}

    labels = [str(dict(row).get(columns[0], "")) for row in rows]
    datasets = []
    palette = [
        "#f97316",
        "#facc15",
        "#38bdf8",
        "#34d399",
    ]
    for index, col in enumerate(numeric_columns[:3]):
        datasets.append(
            {
                "label": col.replace("_", " ").title(),
                "data": [float(dict(row).get(col, 0) or 0) for row in rows],
                "backgroundColor": palette[index % len(palette)],
                "borderColor": palette[index % len(palette)],
                "borderWidth": 2,
            }
        )

    return {
        "type": choose_chart_type(labels, len(datasets)),
        "labels": labels,
        "datasets": datasets,
    }


def format_results(rows: list[sqlite3.Row], columns: list[str]) -> str:
    header = " | ".join(columns)
    divider = "-" * min(80, max(20, len(header)))
    rendered_rows = [" | ".join(str(dict(row).get(col, "")) for col in columns) for row in rows]
    return "\n".join([header, divider, *rendered_rows])


def summarize_rows(question: str, rows: list[sqlite3.Row], columns: list[str]) -> str:
    if not rows:
        return f"No se encontraron resultados para: {question}"
    preview_bits = []
    first_row = dict(rows[0])
    for column in columns[:2]:
        if column in first_row:
            preview_bits.append(f"{column}={first_row[column]}")
    preview = ", ".join(preview_bits)
    return f"Se encontraron {len(rows)} fila(s). Primer resultado: {preview}."


def sql_generator(state: State):
    question = state.get("question", "")
    if IS_DEMO_MODE:
        query = demo_query_for(question)
        if not query:
            return {
                "sql_query": "NONE",
                "error": "No tengo una respuesta predefinida para esa pregunta en modo demo. Prueba con ventas por ciudad, mejores clientes o recaudacion total.",
                "mode": "DEMO",
            }
        return {"sql_query": query, "mode": "DEMO"}

    prompt = f"""You are a SQL expert. Based on the following schema, generate a SQLite query to answer the user's question.
Schema:
{DB_SCHEMA}

User Question: {question}

Return ONLY the SQL query. Use a single safe SELECT statement.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"sql_query": response.content.strip(), "mode": "LIVE"}


def sql_executor(state: State):
    query = state.get("sql_query", "")
    if query == "NONE":
        return {
            "execution_results": "N/A",
            "chart_data": {},
            "error": state.get("error", "Consulta no valida"),
            "row_count": 0,
            "columns": [],
        }

    try:
        safe_query = sanitize_sql(query)
        if not settings.database_path.exists():
            raise FileNotFoundError(f"Database not found: {settings.database_path}")

        conn = sqlite3.connect(settings.database_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(safe_query).fetchall()
        conn.close()

        if not rows:
            return {
                "sql_query": safe_query,
                "execution_results": "No se encontraron resultados.",
                "chart_data": {},
                "error": "",
                "row_count": 0,
                "columns": [],
            }

        columns = list(rows[0].keys())
        return {
            "sql_query": safe_query,
            "execution_results": format_results(rows, columns),
            "chart_data": build_chart_data(rows, columns),
            "error": "",
            "row_count": len(rows),
            "columns": columns,
            "summary": summarize_rows(state.get("question", ""), rows, columns),
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "execution_results": f"Error: {exc}",
            "chart_data": {},
            "row_count": 0,
            "columns": [],
        }


def narrator(state: State):
    if IS_DEMO_MODE:
        if state.get("error"):
            return {
                "final_answer": (
                    "[DEMO MODE] Hubo un problema tecnico: "
                    f"{state['error']}. Revisa la consulta o intenta una sugerencia del dashboard."
                )
            }
        summary = state.get("summary") or "Consulta completada correctamente."
        return {
            "final_answer": (
                "[DEMO MODE] Analisis completado.\n\n"
                f"{summary}\n\n"
                "La tabla y la visualizacion muestran los datos crudos para que puedas auditarlos rapidamente."
            )
        }

    if state.get("error"):
        prompt = (
            f"The user asked: {state.get('question', '')}. The SQL query was: {state.get('sql_query', '')}. "
            f"However, there was an error: {state['error']}. Explain this politely to the user."
        )
    else:
        prompt = f"""You are a BI Analyst. Based on the user's question and the results from the database, provide a clear and insightful answer.

Question: {state.get('question', '')}
SQL Query: {state.get('sql_query', '')}
Results:
{state.get('execution_results', '')}

Provide a concise friendly narration of the data.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_answer": response.content}


workflow = StateGraph(State)
workflow.add_node("sql_generator", sql_generator)
workflow.add_node("sql_executor", sql_executor)
workflow.add_node("narrator", narrator)
workflow.set_entry_point("sql_generator")
workflow.add_edge("sql_generator", "sql_executor")
workflow.add_edge("sql_executor", "narrator")
workflow.add_edge("narrator", END)

graph = workflow.compile()
