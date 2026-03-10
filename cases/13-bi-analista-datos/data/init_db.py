import sqlite3
import os

def init_db():
    db_path = "cases/13-bi-analista-datos/data/bi_database.sqlite"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        category TEXT,
        price REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        city TEXT,
        email TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        product_id INTEGER,
        quantity INTEGER,
        sale_date TEXT,
        total_amount REAL,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    
    # Insert sample data
    products = [
        (1, 'Laptop Pro', 'Electronics', 1200.0),
        (2, 'Smartphone X', 'Electronics', 800.0),
        (3, 'Desk Chair', 'Furniture', 150.0),
        (4, 'Coffee Maker', 'Appliances', 50.0),
        (5, 'Monitor 4K', 'Electronics', 350.0)
    ]
    cursor.executemany("INSERT OR IGNORE INTO products VALUES (?,?,?,?)", products)
    
    customers = [
        (1, 'Alice Smith', 'New York', 'alice@example.com'),
        (2, 'Bob Johnson', 'Los Angeles', 'bob@example.com'),
        (3, 'Charlie Brown', 'Chicago', 'charlie@example.com'),
        (4, 'Diana Prince', 'New York', 'diana@example.com')
    ]
    cursor.executemany("INSERT OR IGNORE INTO customers VALUES (?,?,?,?)", customers)
    
    sales = [
        (1, 1, 1, '2023-10-01', 1200.0),
        (2, 2, 2, '2023-10-02', 1600.0),
        (3, 3, 5, '2023-10-03', 750.0),
        (4, 4, 10, '2023-10-04', 500.0),
        (5, 5, 2, '2023-10-05', 700.0),
        (6, 1, 1, '2023-10-06', 1200.0)
    ]
    cursor.executemany("INSERT OR IGNORE INTO sales VALUES (?,?,?,?,?)", sales)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()
