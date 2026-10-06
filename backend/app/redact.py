"""Last safety net: hide email-like strings and long digit runs before any reply is sent."""
import re

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
# 10+ consecutive digits, optional +country code. Tracking numbers (TRK...), order IDs and
# dates are not matched because they have letters or hyphens around the digits.
PHONE_RE = re.compile(r"(?<![\w.])(?:\+\d{1,3}[\s-]?)?\d{10,}(?!\w)")


def redact(text: str) -> str:
    text = EMAIL_RE.sub("[hidden]", text)
    return PHONE_RE.sub("[hidden]", text)