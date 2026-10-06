import logging
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import SESSION_TTL_MINUTES, VERIFY_LIMIT_PER_10MIN
from .db import build_database, get_conn
from . import tools, sessions, security, engine
from .nlu import classifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("app")

app = FastAPI(title="Customer Query System")


@app.on_event("startup")
def startup():
    build_database()
    classifier.train_classifier()


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:")
    return response


class VerifyBody(BaseModel):
    customer_id: str
    order_id: str


class LogoutBody(BaseModel):
    token: str


class ChatBody(BaseModel):
    message: str = ""

def _bearer(authorization):
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/verify")
def verify(body: VerifyBody, request: Request):
    ip = security.client_ip(request)
    cid = body.customer_id.strip().upper()
    oid = body.order_id.strip().upper()

    if security.rate_limited("verify", ip, VERIFY_LIMIT_PER_10MIN, 600):
        return JSONResponse(status_code=429, content={
            "detail": "Too many attempts. Please wait a few minutes and try again."})

    ip_key, cid_key = f"ip:{ip}", f"cid:{cid}"
    if sessions.is_locked(ip_key) or sessions.is_locked(cid_key):
        return JSONResponse(status_code=429, content={
            "detail": "Too many failed attempts. Please try again in a few minutes."})

    conn = get_conn()
    try:
        ok = tools.verify_customer(conn, cid, oid)
        if not ok:
            sessions.record_failure(ip_key)
            sessions.record_failure(cid_key)
            log.info("verify fail cust=%s status=401", security.mask_id(cid))
            # generic message: never reveal whether the ID exists
            raise HTTPException(status_code=401,
                                detail="We could not verify those details.")
        sessions.clear_failures(ip_key)
        sessions.clear_failures(cid_key)
        token = sessions.create_session(cid)
        first_name = tools.get_first_name(conn, cid)
    finally:
        conn.close()

    log.info("verify ok cust=%s status=200", security.mask_id(cid))
    return {"token": token, "first_name": first_name,
            "expires_in": SESSION_TTL_MINUTES * 60}


@app.post("/api/logout")
def logout(body: LogoutBody):
    sessions.delete_session(body.token)
    return {"ok": True}


@app.get("/api/samples")
def samples():
    """Demo credentials for the evaluator panel: customer ID + one of their orders."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT customer_id, MIN(order_id) AS order_id FROM orders "
            "GROUP BY customer_id ORDER BY customer_id LIMIT 3").fetchall()
        creds = [{"customer_id": r["customer_id"], "order_id": r["order_id"]}
                 for r in rows]
    finally:
        conn.close()
    return {
        "credentials": creds,
        "questions": [
            "Where is my order?",
            "Can I cancel my order?",
            "Show my recent orders",
            "What is the status of my ticket?",
        ],
    }

@app.post("/api/chat")
def chat(request: Request, body: ChatBody = None,
         authorization: str = Header(default=None)):
    token = _bearer(authorization)
    cid = sessions.get_session_customer(token) if token else None
    if not cid:
        raise HTTPException(status_code=401,
                            detail="Session expired, please verify again.")

    ip = security.client_ip(request)
    if security.rate_limited("chat", ip, 60, 60):
        return JSONResponse(status_code=429, content={
            "detail": "You're sending messages too fast. Please wait a moment."})

    message = body.message if body else ""
    conn = get_conn()
    try:
        first_name = tools.get_first_name(conn, cid)
        result = engine.answer(conn, cid, first_name, message)
    finally:
        conn.close()

    # log only intent and a masked ID, never the message text
    log.info("chat cust=%s intent=%s status=200",
             security.mask_id(cid), result["intent"])
    return result
from pathlib import Path
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="web")