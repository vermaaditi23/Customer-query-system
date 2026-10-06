import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import sessions, security, tools
from app.db import get_conn


@pytest.fixture()
def client():
    with TestClient(app) as c:   # runs startup, builds the DB
        sessions.reset_all()
        security.reset_limits()
        yield c


def _creds():
    conn = get_conn()
    r = conn.execute("SELECT customer_id, order_id FROM orders LIMIT 1").fetchone()
    other = conn.execute("SELECT customer_id FROM customers WHERE customer_id != ? "
                         "LIMIT 1", (r["customer_id"],)).fetchone()
    conn.close()
    return r["customer_id"], r["order_id"], other["customer_id"]


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_verify_success_and_chat(client):
    cid, oid, _ = _creds()
    r = client.post("/api/verify", json={"customer_id": cid, "order_id": oid})
    assert r.status_code == 200
    token = r.json()["token"]
    assert set(r.json().keys()) == {"token", "first_name", "expires_in"}
    c = client.post("/api/chat", headers={"Authorization": f"Bearer {token}"})
    assert c.status_code == 200


def test_wrong_order_for_customer(client):
    cid, oid, other = _creds()
    r = client.post("/api/verify", json={"customer_id": other, "order_id": oid})
    assert r.status_code == 401
    assert "could not verify" in r.json()["detail"].lower()


def test_chat_without_or_bad_token(client):
    assert client.post("/api/chat").status_code == 401
    assert client.post("/api/chat",
                       headers={"Authorization": "Bearer fake"}).status_code == 401


def test_lockout_after_failures(client):
    cid, oid, _ = _creds()
    codes = [client.post("/api/verify",
                         json={"customer_id": cid, "order_id": "ORD99999"}).status_code
             for _ in range(6)]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429


def test_expired_token(client):
    cid, oid, _ = _creds()
    token = client.post("/api/verify",
                        json={"customer_id": cid, "order_id": oid}).json()["token"]
    sessions._sessions[token]["expires_at"] = 0
    assert client.post("/api/chat",
                       headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_redaction():
    assert "[hidden]" in security.redact("mail me at user001@example.com")
    assert "[hidden]" in security.redact("call +919000000001 now")
    assert security.redact("Tracking TRK12345678") == "Tracking TRK12345678"