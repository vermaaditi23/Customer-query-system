"""Message in, safe reply out. Uses only the customer_id from the server-side session."""
from app import responses as R
from app import tools
from app.nlu import classifier, entities
from app.redact import redact
from app.llm import answer_general, rephrase_answer

ORDER_INTENTS = {"order_status", "track_order", "delivery_date", "cancel_order",
                 "return_eligibility", "warranty", "payment_refund", "order_details"}


def _pack(intent, text):
    text = rephrase_answer(text)
    return {"reply": redact(text), "intent": intent,
            "suggestions": R.SUGGESTIONS.get(intent, R.SUGGESTIONS["help"])}


def _is_cancelled(order):
    return str(order.get("status") or "").lower().startswith("cancel")


def _is_delivered(order):
    return str(order.get("status") or "").lower() == "delivered"


def _product_text(p):
    return R.pick("product", name=p["product_name"], price=R.fmt_money(p.get("price")),
                  warranty=R.months(p.get("warranty_months")),
                  returnable="Yes" if p.get("returnable") else "No")


def _item_products(conn, cid, order):
    out = []
    for it in tools.get_order_items(conn, cid, order["order_id"]):
        p = tools.get_product(conn, it["product_id"])
        if p:
            out.append((it, p))
    return out


def _lines_for_items(conn, cid, order):
    lines = []
    for it, p in _item_products(conn, cid, order):
        lines.append(f"- {it.get('quantity', 1)} x {p['product_name']} ({R.fmt_money(it.get('unit_price'))} each)")
    return "\n".join(lines) or "- (no items found)"


def _order_answer(intent, order, conn, cid):
    oid = order["order_id"]
    status = order.get("status") or "unknown"
    if intent == "order_status":
        if _is_cancelled(order) or _is_delivered(order):
            return R.pick("order_status_closed", order_id=oid, status=status,
                          order_date=R.fmt_date(order.get("order_date")))
        return R.pick("order_status", order_id=oid, status=status,
                      order_date=R.fmt_date(order.get("order_date")),
                      expected=R.fmt_date(order.get("expected_delivery")))
    if intent == "track_order":
        tn = (order.get("tracking_number") or "").strip()
        return R.pick("track" if tn else "track_none", order_id=oid, tracking=tn)
    if intent == "delivery_date":
        if _is_cancelled(order):
            return R.pick("delivery_cancelled", order_id=oid)
        if _is_delivered(order):
            return R.pick("delivery_done", order_id=oid)
        return R.pick("delivery", order_id=oid, expected=R.fmt_date(order.get("expected_delivery")))
    if intent == "cancel_order":
        if _is_cancelled(order):
            return R.pick("cancel_already", order_id=oid)
        ok = bool(order.get("cancellable")) and not _is_delivered(order)
        return R.pick("cancel_yes" if ok else "cancel_no", order_id=oid, status=status)
    if intent == "return_eligibility":
        if _is_cancelled(order):
            return R.pick("return_cancelled", order_id=oid)
        if not _is_delivered(order):
            return R.pick("return_not_delivered", order_id=oid, status=status)
        blocked = [p["product_name"] for _, p in _item_products(conn, cid, order) if not p.get("returnable")]
        if blocked:
            return R.pick("return_blocked", order_id=oid, items=", ".join(blocked))
        return R.pick("return_ok", order_id=oid)
    if intent == "warranty":
        lines = [f"- {p['product_name']}: {R.months(p.get('warranty_months'))} warranty"
                 for _, p in _item_products(conn, cid, order)]
        return f"Warranty for the items in order {oid}:\n" + ("\n".join(lines) or "- (no items found)")
    if intent == "payment_refund":
        key = "payment_cancelled" if _is_cancelled(order) else "payment"
        return R.pick(key, order_id=oid, payment_status=order.get("payment_status"),
                      payment_method=order.get("payment_method"), total=R.fmt_money(order.get("total_amount")))
    # order_details
    return R.pick("order_details", order_id=oid, status=status,
                  total=R.fmt_money(order.get("total_amount")), lines=_lines_for_items(conn, cid, order))


def answer(conn, customer_id, first_name, message):
    message = (message or "").strip()[:500]
    if not message:
        return _pack("fallback", R.pick("fallback"))
    intent, _conf = classifier.classify(message)

    if intent == "sensitive_request":
                return _pack("sensitive_request", R.pick("sensitive"), polish=False)
    if intent == "greeting":
                return _pack("greeting", R.pick("greeting", first_name=first_name or "there"), polish=False)
    if intent == "help":
                return _pack("help", R.pick("help"), polish=False)
    if intent in ("fallback", "out_of_scope"):
        text = answer_general(message)
        if text:
            return _pack("fallback", text)
        return _pack("fallback", R.pick("fallback"))

    ents = entities.extract(message, entities.load_products(conn))

    if intent == "my_orders":
        orders = tools.list_recent_orders(conn, customer_id)[:5]
        if not orders:
            return _pack(intent, R.pick("no_orders"))
        lines = "\n".join(f"- {o['order_id']}: {o['status']}, {R.fmt_money(o.get('total_amount'))} "
                          f"({R.fmt_date(o.get('order_date'))})" for o in orders)
        return _pack(intent, R.pick("my_orders", lines=lines))

    if intent == "ticket_status":
        if ents["ticket_id"]:
            t = tools.get_ticket(conn, customer_id, ents["ticket_id"])
            if not t:
                return _pack(intent, R.pick("ticket_not_found"))
            return _pack(intent, R.pick("ticket", ticket_id=t["ticket_id"], issue_type=t.get("issue_type"),
                                        status=t.get("status"), priority=t.get("priority"),
                                        created=R.fmt_date(t.get("created_at"))))
        tickets = tools.list_tickets(conn, customer_id)
        if not tickets:
            return _pack(intent, R.pick("no_tickets"))
        lines = "\n".join(f"- {t['ticket_id']}: {t.get('issue_type')}, {t.get('status')}" for t in tickets[:5])
        return _pack(intent, R.pick("my_tickets", lines=lines))

    # product questions that don't need an order
    if intent in ("product_info", "warranty", "return_eligibility") and ents["product_id"] and not ents["order_id"]:
        p = tools.get_product(conn, ents["product_id"])
        if p:
            return _pack(intent, _product_text(p))
    if intent == "product_info":
        return _pack(intent, R.pick("which_product"))

    if intent in ORDER_INTENTS:
        if ents["order_id"]:
            order = tools.get_order(conn, customer_id, ents["order_id"])
            if not order:
                return _pack(intent, R.pick("order_not_found"))
        else:
            recent = tools.list_recent_orders(conn, customer_id)
            if not recent:
                return _pack(intent, R.pick("no_orders"))
            order = tools.get_order(conn, customer_id, recent[0]["order_id"])
            if not order:
                return _pack(intent, R.pick("no_orders"))
        return _pack(intent, _order_answer(intent, order, conn, customer_id))

    return _pack("fallback", R.pick("fallback"))
