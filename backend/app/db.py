import csv
import sqlite3
from .config import DB_PATH, find_csv_dir

SCHEMA = """
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY, name TEXT, email TEXT, phone TEXT,
    city TEXT, state TEXT, pincode TEXT, customer_tier TEXT, created_at TEXT
);
CREATE TABLE products (
    product_id TEXT PRIMARY KEY, product_name TEXT, category TEXT,
    price REAL, stock_quantity INTEGER, warranty_months INTEGER, returnable INTEGER
);
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY, customer_id TEXT, status TEXT, total_amount REAL,
    payment_status TEXT, payment_method TEXT, order_date TEXT,
    expected_delivery TEXT, cancellable INTEGER, tracking_number TEXT
);
CREATE TABLE order_items (
    order_item_id TEXT PRIMARY KEY, order_id TEXT, product_id TEXT,
    quantity INTEGER, unit_price REAL
);
CREATE TABLE support_tickets (
    ticket_id TEXT PRIMARY KEY, customer_id TEXT, order_id TEXT, issue_type TEXT,
    description TEXT, priority TEXT, status TEXT, assigned_to TEXT, created_at TEXT
);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_items_product ON order_items(product_id);
CREATE INDEX idx_tickets_customer ON support_tickets(customer_id);
CREATE INDEX idx_tickets_order ON support_tickets(order_id);
"""

TABLES = {
    "customers": ["customer_id", "name", "email", "phone", "city", "state",
                  "pincode", "customer_tier", "created_at"],
    "products": ["product_id", "product_name", "category", "price",
                 "stock_quantity", "warranty_months", "returnable"],
    "orders": ["order_id", "customer_id", "status", "total_amount", "payment_status",
               "payment_method", "order_date", "expected_delivery", "cancellable",
               "tracking_number"],
    "order_items": ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
    "support_tickets": ["ticket_id", "customer_id", "order_id", "issue_type",
                        "description", "priority", "status", "assigned_to", "created_at"],
}

BOOL_COLS = {"cancellable", "returnable"}
INT_COLS = {"stock_quantity", "warranty_months", "quantity"}
REAL_COLS = {"price", "total_amount", "unit_price"}


def _to_bool(v):
    return 1 if str(v).strip().lower() in ("true", "1", "yes", "y") else 0


def _clean(col, v):
    v = (v or "").strip()
    if col in BOOL_COLS:
        return _to_bool(v)
    if v == "":
        return None
    if col in INT_COLS:
        return int(float(v))
    if col in REAL_COLS:
        return float(v)
    return v


def build_database():
    csv_dir = find_csv_dir()
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    for table, cols in TABLES.items():
        with open(csv_dir / f"{table}.csv", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = [[_clean(c, r.get(c)) for c in cols] for r in reader]
        marks = ",".join("?" * len(cols))
        conn.executemany(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({marks})", rows)
    conn.commit()
    conn.close()


def get_conn():
    """Read-only connection: the app can never modify data."""
    conn = sqlite3.connect(DB_PATH.as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == "__main__":
    build_database()
    conn = get_conn()
    for t in TABLES:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}: {n} rows")
    blanks = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE tracking_number IS NULL").fetchone()[0]
    print(f"orders with no tracking number: {blanks}")
    print("sample order:", dict(conn.execute("SELECT * FROM orders LIMIT 1").fetchone()))
    conn.close()