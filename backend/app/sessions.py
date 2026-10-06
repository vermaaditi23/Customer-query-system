"""In-memory sessions and failed-attempt lockouts."""
import secrets
import time
from .config import SESSION_TTL_MINUTES, MAX_FAILED_VERIFY, LOCKOUT_MINUTES

_sessions = {}   # token -> {"customer_id": str, "expires_at": float}
_failures = {}   # key (ip or customer id) -> {"count": int, "locked_until": float}


def create_session(customer_id: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "customer_id": customer_id,
        "expires_at": time.time() + SESSION_TTL_MINUTES * 60,
    }
    return token


def get_session_customer(token: str):
    """Return customer_id if the token is valid, else None. Extends the TTL on use."""
    s = _sessions.get(token)
    if not s:
        return None
    if s["expires_at"] < time.time():
        _sessions.pop(token, None)
        return None
    s["expires_at"] = time.time() + SESSION_TTL_MINUTES * 60  # inactivity timeout
    return s["customer_id"]


def delete_session(token: str):
    _sessions.pop(token, None)


def is_locked(key: str) -> bool:
    f = _failures.get(key)
    if not f:
        return False
    if f["locked_until"] > time.time():
        return True
    if f["locked_until"] and f["locked_until"] <= time.time():
        _failures.pop(key, None)  # lockout finished
    return False


def record_failure(key: str):
    f = _failures.setdefault(key, {"count": 0, "locked_until": 0.0})
    f["count"] += 1
    if f["count"] >= MAX_FAILED_VERIFY:
        f["locked_until"] = time.time() + LOCKOUT_MINUTES * 60


def clear_failures(key: str):
    _failures.pop(key, None)


def reset_all():
    """Used by tests."""
    _sessions.clear()
    _failures.clear()