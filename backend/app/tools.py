"""Safe query functions. Privacy rules enforced here:
- customer_id always comes from the verified session, never from chat text
- only allow-listed columns are selected (no SELECT *)
- every query on a private table has WHERE customer_id = ?
- an order owned by someone else returns None, same as a missing order
"""

ORDER_COLS = ("order_id, status, payment_status, payment_method, order_date, "
              "expected_delivery, cancellable, tracking_number, total_amount")
TICKET_COLS = ("ticket_id, order_id, issue_type, description, priority, "
               "status, created_at")
PRODUCT_COLS = ("product_id, product_name, category, price, "
                "warranty_months, returnable")  # stock_quantity is hidden


def _one(conn, sql, params):
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def _all(conn, sql, params):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ---------- verification ----------
def verify_customer(conn, customer_id, order_id):
    """True only if the order belongs to that customer."""
    row = conn.execute(
        "SELECT 1 FROM orders WHERE order_id = ? AND customer_id = ?",
        (order_id.strip().upper(), customer_id.strip().upper())).fetchone()
    return row is not None


def get_first_name(conn, customer_id):
    row = conn.execute(
        "SELECT name FROM customers WHERE customer_id = ?",
        (customer_id,)).fetchone()
    if not row or not row["name"]:
        return "there"
    return row["name"].split()[0]


# ---------- orders ----------
def get_order(conn, customer_id, order_id):
    return _one(conn,
        f"SELECT {ORDER_COLS} FROM orders WHERE order_id = ? AND customer_id = ?",
        (order_id.upper(), customer_id))


def list_recent_orders(conn, customer_id, limit=5):
    return _all(conn,
        f"SELECT {ORDER_COLS} FROM orders WHERE customer_id = ? "
        "ORDER BY order_date DESC LIMIT ?", (customer_id, limit))


def get_order_items(conn, customer_id, order_id):
    # join through orders so the owner check is built in
    return _all(conn,
        "SELECT p.product_id, p.product_name, oi.quantity, oi.unit_price "
        "FROM order_items oi "
        "JOIN orders o ON o.order_id = oi.order_id "
        "JOIN products p ON p.product_id = oi.product_id "
        "WHERE oi.order_id = ? AND o.customer_id = ?",
        (order_id.upper(), customer_id))


# ---------- tickets ----------
def get_ticket(conn, customer_id, ticket_id):
    return _one(conn,
        f"SELECT {TICKET_COLS} FROM support_tickets "
        "WHERE ticket_id = ? AND customer_id = ?",
        (ticket_id.upper(), customer_id))


def list_tickets(conn, customer_id, limit=5):
    return _all(conn,
        f"SELECT {TICKET_COLS} FROM support_tickets WHERE customer_id = ? "
        "ORDER BY created_at DESC LIMIT ?", (customer_id, limit))


# ---------- products (public) ----------
def get_product(conn, product_id):
    return _one(conn,
        f"SELECT {PRODUCT_COLS} FROM products WHERE product_id = ?",
        (product_id,))


def list_products(conn):
    return _all(conn, f"SELECT {PRODUCT_COLS} FROM products", ())


def get_warranty(conn, product_id):
    p = get_product(conn, product_id)
    return None if not p else {"product_name": p["product_name"],
                               "warranty_months": p["warranty_months"]}


# ---------- return eligibility ----------
def check_return_eligibility(conn, customer_id, order_id):
    """Order status + product returnable flag. Returns None if order not yours."""
    order = get_order(conn, customer_id, order_id)
    if not order:
        return None
    items = _all(conn,
        "SELECT p.product_name, p.returnable FROM order_items oi "
        "JOIN products p ON p.product_id = oi.product_id "
        "WHERE oi.order_id = ?", (order["order_id"],))
    delivered = str(order["status"]).lower() == "delivered"
    non_returnable = [i["product_name"] for i in items if not i["returnable"]]
    return {
        "order_id": order["order_id"],
        "status": order["status"],
        "delivered": delivered,
        "non_returnable": non_returnable,
        "eligible": delivered and not non_returnable,
    }