"""Reply templates (random variants), formatting helpers and suggestion chips."""
import random
from datetime import datetime


def fmt_date(value) -> str:
    if not value:
        return "not available yet"
    try:
        d = datetime.fromisoformat(str(value)[:10])
        return f"{d.day} {d:%b %Y}"
    except ValueError:
        return str(value)


def fmt_money(value) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "not available"


def months(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "no"
    return f"{n} month" + ("" if n == 1 else "s")


TEMPLATES = {
    "greeting": [
        "Hi {first_name}! I can help with your orders, tickets, returns and warranty. What would you like to know?",
        "Hello {first_name}! Ask me about an order, a ticket, a return or a product.",
    ],
    "help": [
        "I can help with: order status, tracking, delivery dates, cancellation, returns, warranty, "
        "payments and refunds, your support tickets, and product prices.",
    ],
    "fallback": [
        "Sorry, I didn't quite get that. I can help with order status, tracking, cancellation, returns, "
        "warranty, tickets and product info.",
        "I'm not sure I understood. Try something like \"Where is my order ORD00002?\" or \"Warranty for the Bluetooth Speaker\".",
    ],
    "sensitive": [
        "I can't share personal details like contact information or other customers' data. "
        "I can help with your orders, tickets, returns and warranty.",
    ],
    "order_not_found": [
        "I couldn't find that order on your account. Please check the order ID, or say \"show my recent orders\".",
    ],
    "no_orders": ["I couldn't find any orders on your account yet."],
    "ticket_not_found": [
        "I couldn't find that ticket on your account. Say \"show my tickets\" to see yours.",
    ],
    "no_tickets": ["You don't have any support tickets on your account."],
    "which_product": [
        "Which product do you mean? You can say the name, for example \"price of Bluetooth Speaker\".",
    ],
    "order_status": [
        "Your order {order_id} is currently {status}. It was placed on {order_date} and is expected by {expected}.",
        "Order {order_id} is {status}. Placed on {order_date}, expected delivery {expected}.",
    ],
    "order_status_closed": [
        "Your order {order_id} is {status}. It was placed on {order_date}.",
    ],
    "track": [
        "The tracking number for order {order_id} is {tracking}.",
        "Order {order_id} is on its way. Tracking number: {tracking}.",
    ],
    "track_none": [
        "Order {order_id} hasn't shipped yet, so there's no tracking number. I'll show it here as soon as it's available.",
        "There's no tracking number for {order_id} yet. Tracking will be available once the order ships.",
    ],
    "delivery": [
        "Order {order_id} is expected by {expected}.",
        "You can expect order {order_id} around {expected}.",
    ],
    "delivery_done": ["Order {order_id} has already been delivered."],
    "delivery_cancelled": ["Order {order_id} was cancelled, so it won't be delivered."],
    "cancel_yes": [
        "Order {order_id} is {status} and is still eligible for cancellation. I can't cancel it from this chat, "
        "so please contact support with the order ID to go ahead.",
    ],
    "cancel_no": [
        "Order {order_id} is {status} and can no longer be cancelled.",
    ],
    "cancel_already": ["Order {order_id} is already cancelled."],
    "return_ok": [
        "Order {order_id} was delivered and all its items are returnable, so you can request a return.",
    ],
    "return_blocked": [
        "Order {order_id} was delivered, but these items can't be returned: {items}.",
    ],
    "return_not_delivered": [
        "Order {order_id} is {status}. Returns can be requested only after delivery.",
    ],
    "return_cancelled": ["Order {order_id} was cancelled, so there is nothing to return."],
    "payment": [
        "For order {order_id}, the payment status is {payment_status} (paid via {payment_method}). Order total: {total}.",
    ],
    "payment_cancelled": [
        "Order {order_id} was cancelled. Payment status: {payment_status} (via {payment_method}). "
        "Any refund due goes back to the original payment method.",
    ],
        "refund_howto": [
        "To get a refund, first check that your order is delivered and its items are returnable "
        "(ask me \"Can I return my order?\"). Then raise a support ticket with the order ID. "
        "Approved refunds go back to the original payment method. "
        "You can also ask me for your payment status.",
    ],
    "order_details": ["Order {order_id} ({status}), total {total}:\n{lines}"],
    "my_orders": ["Here are your most recent orders:\n{lines}"],
    "ticket": [
        "Ticket {ticket_id} ({issue_type}) is currently {status}, priority {priority}. It was opened on {created}.",
    ],
    "my_tickets": ["Here are your support tickets:\n{lines}"],
    "product": [
        "{name}: {price}. Warranty: {warranty}. Returnable: {returnable}.",
        
    ],
}


def pick(key: str, **kw) -> str:
    return random.choice(TEMPLATES[key]).format(**kw)


SUGGESTIONS = {
    "greeting": ["Show my recent orders", "Track my order", "My tickets"],
    "help": ["Show my recent orders", "Return policy", "My tickets"],
    "fallback": ["Show my recent orders", "Track my order", "What can you do?"],
    "sensitive_request": ["Show my recent orders", "My tickets", "What can you do?"],
    "order_status": ["Track my order", "Can I cancel it?", "What is in my order?"],
    "track_order": ["When will it arrive?", "Payment status", "My tickets"],
    "delivery_date": ["Track my order", "Can I cancel it?", "Payment status"],
    "cancel_order": ["Order status", "Payment status", "My tickets"],
    "return_eligibility": ["Warranty details", "What is in my order?", "My tickets"],
    "warranty": ["Is it returnable?", "Show my recent orders", "My tickets"],
    "payment_refund": ["Order status", "Can I cancel it?", "My tickets"],
    "order_details": ["Track my order", "Is it returnable?", "Warranty details"],
    "my_orders": ["Track my order", "My tickets", "Return policy"],
    "ticket_status": ["Show my recent orders", "Track my order", "What can you do?"],
    "product_info": ["Is it returnable?", "Warranty details", "Show my recent orders"],
}