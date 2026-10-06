import pytest
from app.nlu import classifier
from app.nlu.entities import extract, load_products
from app.db import build_database, get_conn


def test_holdout_accuracy():
    data = classifier.load_phrases()
    train_x, train_y, test_x, test_y = [], [], [], []
    for intent, phrases in data.items():
        for i, p in enumerate(phrases):
            if i % 5 == 0:          # every 5th phrase is held out (20%)
                test_x.append(p); test_y.append(intent)
            else:
                train_x.append(p); train_y.append(intent)
    model = classifier.build_model(train_x, train_y)
    pred = [model.predict(t)[0] for t in test_x]
    acc = sum(1 for a, b in zip(pred, test_y) if a == b) / len(test_y)
    print("holdout accuracy:", acc)
    assert acc >= 0.75


@pytest.mark.parametrize("text,expected", [
    ("Can I cancel ORD00001?", "cancel_order"),
    ("What is the tracking number", "track_order"),
    ("Show my recent orders", "my_orders"),
    ("warranty for the speaker", "warranty"),
    ("hi", "greeting"),
])
def test_known_phrases(text, expected):
    assert classifier.classify(text)[0] == expected


def test_nonsense_gets_fallback():
    assert classifier.classify("asdkjh qwerty zzzz")[0] == "fallback"


def test_entities_and_fuzzy_product():
    build_database()
    conn = get_conn()
    products = load_products(conn)
    conn.close()
    pid, name = products[0]
    typo = (name[:3] + name[4:]).lower()     # drop one letter
    found = extract(f"is the {typo} returnable", products)
    assert found["product_id"] == pid
    e = extract("status of ord00002 and tkt00001", products)
    assert e["order_id"] == "ORD00002" and e["ticket_id"] == "TKT00001"