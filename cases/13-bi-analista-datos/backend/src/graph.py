from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import sqlite3
from .settings import settings

# Define the state
class State(TypedDict):
    question: str
    sql_query: str
    execution_results: str
    chart_data: dict  # New field for structured data
    final_answer: str
    error: str

# Database schema for the LLM
DB_SCHEMA = """
Tables:
1. products (id, name, category, price)
2. sales (id, product_id, quantity, sale_date, total_amount)
3. customers (id, name, city, email)
"""

# Determine if we are in Demo Mode
IS_DEMO_MODE = not settings.OPENAI_API_KEY

if not IS_DEMO_MODE:
    llm = ChatOpenAI(model="gpt-4o", api_key=settings.OPENAI_API_KEY, timeout=10)
else:
    llm = None

def sql_generator(state: State):
    if IS_DEMO_MODE:
        q = state['question'].lower()
        # Remove accents for easier matching
        q = q.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        if "reciente" in q or "ultimas ventas" in q:
            query = "SELECT s.sale_date, p.name, s.total_amount FROM sales s JOIN products p ON s.product_id = p.id ORDER BY s.sale_date DESC LIMIT 5;"
        elif "caro" in q or "mayor precio" in q:
            query = "SELECT name, price FROM products ORDER BY price DESC LIMIT 1;"
        elif "barato" in q or "menor precio" in q:
            query = "SELECT name, price FROM products ORDER BY price ASC LIMIT 1;"
        elif "vendido" in q or "mas ventas" in q or "mayor venta" in q:
            query = "SELECT p.name, SUM(s.quantity) as total FROM sales s JOIN products p ON s.product_id = p.id GROUP BY p.id ORDER BY total DESC LIMIT 1;"
        elif "menos vendido" in q or "peor producto" in q:
            query = "SELECT p.name, SUM(s.quantity) as total FROM sales s JOIN products p ON s.product_id = p.id GROUP BY p.id ORDER BY total ASC LIMIT 1;"
        elif "ciudad" in q or "por ciudad" in q:
            query = "SELECT c.city, SUM(s.total_amount) as total FROM sales s JOIN customers c ON s.customer_id = c.id GROUP BY c.city ORDER BY total DESC;"
        elif "recaudacion" in q or "ingreso" in q or "ventas totales" in q or "monto total" in q:
            query = "SELECT SUM(total_amount) as gran_total FROM sales;"
        elif "promedio" in q:
            query = "SELECT AVG(total_amount) as promedio FROM sales;"
        elif "categoria" in q or "mejor categoria" in q:
            query = "SELECT p.category, SUM(s.total_amount) as total FROM sales s JOIN products p ON s.product_id = p.id GROUP BY p.category ORDER BY total DESC;"
        elif "mejores clientes" in q or ("cliente" in q and "gasto" in q) or "quien gasto mas" in q:
            query = "SELECT c.name, SUM(s.total_amount) as total FROM sales s JOIN customers c ON s.customer_id = c.id GROUP BY c.id ORDER BY total DESC LIMIT 3;"
        elif "cliente" in q:
            query = "SELECT name, city FROM customers LIMIT 5;"
        elif "producto" in q:
            query = "SELECT name, category, price FROM products LIMIT 5;"
        else:
            return {"sql_query": "NONE", "error": "No tengo una respuesta predefinida para esta pregunta en Modo Demo. Prueba con 'ventas por ciudad', 'mejores clientes' o 'recaudación total'."}
        return {"sql_query": query}
    
    prompt = f"""You are a SQL expert. Based on the following schema, generate a SQLite query to answer the user's question.
    Schema:
    {DB_SCHEMA}
    
    User Question: {state['question']}
    
    Return ONLY the SQL query, no markdown, no explanations.
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    query = response.content.strip().replace("```sql", "").replace("```", "")
    return {"sql_query": query}

def sql_executor(state: State):
    query = state['sql_query']
    if query == "NONE":
        return {"execution_results": "N/A", "chart_data": {}, "error": state.get("error", "Consulta no válida")}
    
    try:
        # Use absolute path inside docker
        conn = sqlite3.connect("/app/data/bi_database.sqlite")
        conn.row_factory = sqlite3.Row # To get column names easily
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            conn.close()
            return {"execution_results": "No se encontraron resultados.", "chart_data": {}, "error": ""}
            
        columns = rows[0].keys()
        conn.close()
        
        # Format results as a simple string table
        res_str = " | ".join(columns) + "\n" + "-" * 20 + "\n"
        chart_data = {"labels": [], "datasets": [{"label": "Valor", "data": []}]}
        
        for row in rows:
            res_str += " | ".join(map(str, row)) + "\n"
            # Logic to extract chart labels and data
            # Typically first column is label, second/all others are values
            row_list = list(row)
            if len(row_list) >= 2:
                chart_data["labels"].append(str(row_list[0]))
                try:
                    # Try to get the numeric value from the last column
                    chart_data["datasets"][0]["data"].append(float(row_list[-1]))
                except:
                    chart_data["datasets"][0]["data"].append(0)
        
        return {"execution_results": res_str, "chart_data": chart_data, "error": ""}
    except Exception as e:
        return {"error": str(e), "execution_results": f"Error: {str(e)}", "chart_data": {}}

def narrator(state: State):
    if IS_DEMO_MODE:
        if state.get("error"):
            return {"final_answer": f"[DEMO MODE] Hubo un problema técnico: {state['error']}. Por favor verifica la consulta SQL."}
        
        res = state['execution_results']
        ans = f"[DEMO MODE] Analizando los datos obtenidos:\n\n{res}\nBasado en la base de datos, he encontrado la información solicitada arriba. (Activa tu API Key para análisis avanzado)."
        return {"final_answer": ans}

    if state.get("error"):
         prompt = f"The user asked: {state['question']}. The SQL query was: {state['sql_query']}. However, there was an error: {state['error']}. Explain this politely to the user."
    else:
        prompt = f"""You are a BI Analyst. Based on the user's question and the results from the database, provide a clear and insightful answer.
        
        Question: {state['question']}
        SQL Query: {state['sql_query']}
        Results:
        {state['execution_results']}
        
        Provide a friendly narration of the data.
        """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_answer": response.content}

# Build the graph
workflow = StateGraph(State)

workflow.add_node("sql_generator", sql_generator)
workflow.add_node("sql_executor", sql_executor)
workflow.add_node("narrator", narrator)

workflow.set_entry_point("sql_generator")
workflow.add_edge("sql_generator", "sql_executor")
workflow.add_edge("sql_executor", "narrator")
workflow.add_edge("narrator", END)

graph = workflow.compile()
