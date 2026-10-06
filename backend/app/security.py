"""Rate limiting, log masking and the output redaction safety net."""
import re
import time
from collections import defaultdict, deque

_hits = defaultdict(deque)  # (bucket, ip) -> timestamps


def rate_limited(bucket: str, ip: str, limit: int, window_seconds: int) -> bool:
    """True if this call is over the limit. Counts the call otherwise."""
    now = time.time()
    q = _hits[(bucket, ip)]
    while q and q[0] < now - window_seconds:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    return False


def reset_limits():
    _hits.clear()


def client_ip(request) -> str:
    """Behind Render / Hugging Face proxies the real IP is in X-Forwarded-For."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def mask_id(customer_id: str) -> str:
    """CUST0005 -> CUST****05 (for logs only)."""
    if not customer_id or len(customer_id) < 6:
        return "****"
    return customer_id[:4] + "****" + customer_id[-2:]


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<![A-Za-z0-9])\+?\d[\d\s\-]{8,}\d(?![A-Za-z0-9])")


def redact(text: str) -> str:
    """Last safety net: hide emails and phone-like numbers in any reply.
    Tracking numbers start with letters (TRK...), so they are not matched."""
    text = EMAIL_RE.sub("[hidden]", text)
    text = PHONE_RE.sub("[hidden]", text)
    return text