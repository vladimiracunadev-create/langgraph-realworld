import sqlite3
from importlib import import_module
from pathlib import Path

init_db_module = import_module('data.init_db')


def test_init_db_creates_expected_schema_and_rows(monkeypatch):
    db_path = Path('cases/13-bi-analista-datos/data/pytest-bi.sqlite').resolve()
    if db_path.exists():
        db_path.unlink()
    monkeypatch.setattr(init_db_module, 'DB_PATH', db_path)

    try:
        result_path = init_db_module.init_db()
        assert result_path == db_path
        assert db_path.exists()

        conn = sqlite3.connect(db_path)
        sales_columns = [row[1] for row in conn.execute('PRAGMA table_info(sales)').fetchall()]
        assert 'customer_id' in sales_columns

        city_rows = conn.execute(
            'SELECT c.city, SUM(s.total_amount) AS total FROM sales s JOIN customers c ON s.customer_id = c.id GROUP BY c.city ORDER BY total DESC'
        ).fetchall()
        conn.close()

        assert city_rows
        assert city_rows[0][0] == 'New York'
    finally:
        if db_path.exists():
            db_path.unlink()
