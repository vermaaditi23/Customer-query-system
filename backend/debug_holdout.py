"""Lists the held-out phrases the classifier gets wrong. Run from the backend folder."""
from app.nlu import classifier

data = classifier.load_phrases()
train_x, train_y, test = [], [], []
for intent, phrases in data.items():
    for i, p in enumerate(phrases):
        if i % 5 == 0:
            test.append((p, intent))
        else:
            train_x.append(p)
            train_y.append(intent)

model = classifier.build_model(train_x, train_y)
print("phrases per intent:", {k: len(v) for k, v in data.items()})

wrong = 0
for p, true in test:
    pred, sim = model.predict(p)
    if pred != true:
        wrong += 1
        print(f"WRONG {p!r}\n      expected={true}  got={pred}  sim={sim:.2f}")
print(f"{len(test) - wrong}/{len(test)} correct")