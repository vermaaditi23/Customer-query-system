from app import responses as R
from app.redact import redact


def test_redacts_email_and_phone():
    assert "[hidden]" in redact("mail me at user001@example.com")
    assert "9000000001" not in redact("call +919000000001 now")
    assert "9000000001" not in redact("call 9000000001 now")


def test_keeps_safe_values():
    s = "Order ORD00002, tracking TRK123456789012, placed 2026-09-16, total ₹1,299.00"
    assert redact(s) == s


def test_formatters():
    assert R.fmt_date("2026-09-16") == "16 Sep 2026"
    assert R.fmt_date("") == "not available yet"
    assert R.fmt_money(1299) == "₹1,299.00"
    assert R.months(1) == "1 month" and R.months(12) == "12 months"


def test_every_template_formats_and_engine_imports():
    from app import engine  # catches import errors in engine.py / tools.py
    assert engine.answer
    assert R.pick("greeting", first_name="Asha")
    assert R.pick("sensitive")