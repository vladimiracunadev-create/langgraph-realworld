import pytest
from importlib import import_module

graph = import_module("backend.src.graph")


def test_demo_query_for_city_sales():
    query = graph.demo_query_for("Ventas por ciudad")
    assert query is not None
    assert "JOIN customers" in query
    assert "GROUP BY c.city" in query


def test_sanitize_sql_rejects_mutation():
    try:
        graph.sanitize_sql("DROP TABLE sales")
    except ValueError as exc:
        assert "Unsafe SQL" in str(exc) or "Only SELECT" in str(exc)
    else:
        raise AssertionError("sanitize_sql should reject destructive statements")


def test_sanitize_sql_adds_limit_when_missing():
    safe = graph.sanitize_sql("SELECT name, price FROM products")
    assert safe.endswith("LIMIT 100")


def test_sanitize_sql_rejects_comments():
    with pytest.raises(ValueError, match="comments are not allowed"):
        graph.sanitize_sql("SELECT name FROM products -- hidden tail")


def test_sanitize_sql_rejects_large_limit():
    with pytest.raises(ValueError, match="LIMIT cannot exceed 100"):
        graph.sanitize_sql("SELECT name FROM products LIMIT 1000")


def test_build_chart_data_uses_numeric_columns():
    rows = [
        {"city": "New York", "total": 100.0},
        {"city": "Chicago", "total": 55.0},
    ]
    chart = graph.build_chart_data(rows, ["city", "total"])
    assert chart["labels"] == ["New York", "Chicago"]
    assert chart["datasets"][0]["data"] == [100.0, 55.0]
