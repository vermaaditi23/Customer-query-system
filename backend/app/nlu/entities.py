"""Pull order IDs, ticket IDs and product names out of a message.
Fuzzy matching uses Python's built-in difflib (no extra packages)."""
import re
from difflib import SequenceMatcher

ORDER_RE = re.compile(r"\bORD\d{3,}\b", re.I)
TICKET_RE = re.compile(r"\bTKT\d{3,}\b", re.I)

STOP_WORDS = {
    "the", "my", "of", "is", "it", "for", "what", "whats", "how", "much", "does",
    "price", "cost", "warranty", "stock", "tell", "about", "this", "that", "have",
    "you", "can", "return", "returnable", "order", "orders", "item", "items",
    "product", "products", "and", "with", "show", "details", "available", "when",
    "will", "status", "ticket", "refund", "cancel", "track", "tracking", "please",
    "want", "need", "are", "was", "there", "any", "from", "your", "here", "get",
}
MATCH_THRESHOLD = 0.85


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _best_window_ratio(gram: str, name: str) -> float:
    """Compare the gram with every run of the same number of words in the name."""
    n_words = len(gram.split())
    name_words = name.split()
    best = 0.0
    for i in range(max(1, len(name_words) - n_words + 1)):
        window = " ".join(name_words[i:i + n_words])
        best = max(best, _ratio(gram, window))
    return best


def load_products(conn):
    rows = conn.execute("SELECT product_id, product_name FROM products").fetchall()
    return [(r["product_id"], r["product_name"]) for r in rows]


def find_product(text: str, products):
    """Fuzzy match so 'bluetooth speker' still finds 'Bluetooth Speaker'."""
    words = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP_WORDS]
    grams = set()
    for n in (1, 2, 3):
        for i in range(len(words) - n + 1):
            grams.add(" ".join(words[i:i + n]))
    best, best_key = None, (0.0, 0.0)
    for g in grams:
        if len(g) < 4:
            continue
        for pid, name in products:
            n = name.lower()
            key = (_best_window_ratio(g, n), _ratio(g, n))
            if key[0] >= MATCH_THRESHOLD and key > best_key:
                best, best_key = pid, key
    return best


def extract(text: str, products):
    order = ORDER_RE.search(text)
    ticket = TICKET_RE.search(text)
    return {
        "order_id": order.group(0).upper() if order else None,
        "ticket_id": ticket.group(0).upper() if ticket else None,
        "product_id": find_product(text, products),
    }