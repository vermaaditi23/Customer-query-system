import sqlite3
import pytest
from app.db import build_database, get_conn
from app import tools


@pytest.fixture(scope="module")
def conn():
    build_database()
    c = get_conn()
    yield c
    c.close()


def _sample(conn):
    row = conn.execute("SELECT order_id, customer_id FROM orders LIMIT 1").fetchone()
    return row["customer_id"], row["order_id"]


def _other_customer(conn, cid):
    return conn.execute(
        "SELECT customer_id FROM customers WHERE customer_id != ? LIMIT 1",
        (cid,)).fetchone()["customer_id"]


def test_owner_can_see_order(conn):
    cid, oid = _sample(conn)
    assert tools.get_order(conn, cid, oid)["order_id"] == oid


def test_other_customer_cannot_see_order(conn):
    cid, oid = _sample(conn)
    assert tools.get_order(conn, _other_customer(conn, cid), oid) is None


def test_verify(conn):
    cid, oid = _sample(conn)
    assert tools.verify_customer(conn, cid, oid)
    assert not tools.verify_customer(conn, _other_customer(conn, cid), oid)


def test_no_sensitive_columns(conn):
    cid, oid = _sample(conn)
    order = tools.get_order(conn, cid, oid)
    assert "customer_id" not in order
    p = tools.list_products(conn)[0]
    assert "stock_quantity" not in p
    t = tools.list_tickets(conn, cid)
    for row in t:
        assert "assigned_to" not in row


def test_sql_injection_safe(conn):
    cid, _ = _sample(conn)
    assert tools.get_order(conn, cid, "ORD1' OR '1'='1") is None


def test_first_name_only(conn):
    cid, _ = _sample(conn)
    name = tools.get_first_name(conn, cid)
    assert " " not in name and "@" not in name