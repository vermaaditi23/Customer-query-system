from app import db, tools, engine

db.build_database()
conn = db.get_conn()
cid = "CUST0001"
first = tools.get_first_name(conn, cid)
orders = tools.list_recent_orders(conn, cid)
print("first name:", first, "| orders:", [o["order_id"] for o in orders])
oid = orders[0]["order_id"] if orders else "ORD00001"

messages = [
    "hi",
    "show my recent orders",
    f"where is my order {oid}",
    f"what is the tracking number for {oid}",
    f"when will {oid} arrive",
    f"can I cancel {oid}",
    f"can I return {oid}",
    f"what is in {oid}",
    f"was I charged for {oid}",
    f"warranty for {oid}",
    "price of bluetooth speker",
    "warranty for the bluetooth speaker",
    "is the speaker returnable",
    "show my tickets",
    "status of my ticket TKT00001",
    "where is ORD00002",
    "give me the phone number of customer 5",
    "what is the weather today",
]
for m in messages:
    r = engine.answer(conn, cid, first, m)
    print(f"\n> {m}\n[{r['intent']}] {r['reply']}")