import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "cases" / "13-bi-analista-datos" / "data" / "bi_database.sqlite"

PRODUCTS = [
    (1, "Laptop Pro", "Electronics", 1200.0),
    (2, "Smartphone X", "Electronics", 800.0),
    (3, "Desk Chair", "Furniture", 150.0),
    (4, "Coffee Maker", "Appliances", 50.0),
    (5, "Monitor 4K", "Electronics", 350.0),
]

CUSTOMERS = [
    (1, "Alice Smith", "New York", "alice@example.com"),
    (2, "Bob Johnson", "Los Angeles", "bob@example.com"),
    (3, "Charlie Brown", "Chicago", "charlie@example.com"),
    (4, "Diana Prince", "New York", "diana@example.com"),
]

SALES = [
    (1, 1, 1, 1, "2023-10-01", 1200.0),
    (2, 2, 2, 2, "2023-10-02", 1600.0),
    (3, 3, 3, 5, "2023-10-03", 750.0),
    (4, 4, 4, 10, "2023-10-04", 500.0),
    (5, 5, 1, 2, "2023-10-05", 700.0),
    (6, 1, 4, 1, "2023-10-06", 1200.0),
    (7, 2, 1, 1, "2023-10-07", 800.0),
]


def ensure_schema(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            city TEXT,
            email TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            customer_id INTEGER,
            quantity INTEGER,
            sale_date TEXT,
            total_amount REAL,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
        """
    )

    sales_columns = [row[1] for row in cursor.execute("PRAGMA table_info(sales)").fetchall()]
    if "customer_id" not in sales_columns:
        cursor.execute("ALTER TABLE sales ADD COLUMN customer_id INTEGER")
        seed_customer_ids = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 1), (6, 4), (7, 1)]
        cursor.executemany("UPDATE sales SET customer_id = ? WHERE id = ?", [(cid, sale_id) for sale_id, cid in seed_customer_ids])


def seed_data(cursor: sqlite3.Cursor) -> None:
    cursor.executemany("INSERT OR REPLACE INTO products VALUES (?,?,?,?)", PRODUCTS)
    cursor.executemany("INSERT OR REPLACE INTO customers VALUES (?,?,?,?)", CUSTOMERS)
    cursor.executemany("INSERT OR REPLACE INTO sales VALUES (?,?,?,?,?,?)", SALES)


def init_db() -> Path:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ensure_schema(cursor)
    seed_data(cursor)
    conn.commit()
    conn.close()
    return DB_PATH


if __name__ == "__main__":
    db_path = init_db()
    print(f"Database initialized at {db_path}")
