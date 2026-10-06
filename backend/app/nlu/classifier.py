"""Intent classifier in pure Python (TF-IDF + cosine similarity) plus the
sensitive-request rules. No scikit-learn, no compiled packages, no LLM."""
import json
import math
import re
from collections import Counter
from pathlib import Path

INTENTS_PATH = Path(__file__).with_name("intents.json")
CONFIDENCE_THRESHOLD = 0.30

SENSITIVE_PATTERNS = [
    r"\be-?mails?\b", r"\bphone\b", r"\bmobile\b", r"\bcontact (number|details|info)",
    r"\baddress(es)?\b", r"\bpin ?codes?\b", r"\bzip\b", r"\bcity\b",
    r"\bwhere (does|do|did)\b.*\blive",
    r"\ball (the )?(customers?|users?)\b",
    r"\b(other|another|different)\s+(customer|user|person|account)",
    r"\bsomeone else",
    r"\bcustomer\s*#?\s*\d+", r"\bcust\d+",
    r"\blist (all )?(the )?(users?|customers?)",
    r"\bignore\b.{0,30}\b(instructions?|rules?|previous|prompt)\b",
    r"\bdatabase\b", r"\bsystem prompt\b", r"\bschema\b",
    r"\bsql\b", r"\bdrop table\b", r"\bselect\b.*\bfrom\b",
    r"\bpassword\b", r"\bcard number\b", r"\bcvv\b",
]
_SENSITIVE_RE = [re.compile(p) for p in SENSITIVE_PATTERNS]

_model = None


def normalise(text: str) -> str:
    text = text.lower().replace("\u2019", "'")
    return re.sub(r"\s+", " ", text).strip()


def prepare(text: str) -> str:
    """Normalise and replace IDs by placeholder words so any ID looks the same."""
    t = normalise(text)
    t = re.sub(r"\bord\d+\b", "ordid", t)
    t = re.sub(r"\btkt\d+\b", "tktid", t)
    return t


def is_sensitive(text: str) -> bool:
    t = normalise(text)
    return any(rx.search(t) for rx in _SENSITIVE_RE)


def load_phrases() -> dict:
    with open(INTENTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _features(text: str) -> Counter:
    """Word, word-pair and character n-gram features (typo friendly)."""
    words = re.findall(r"[a-z0-9']+", prepare(text))
    feats = Counter()
    for w in words:
        feats["w:" + w] += 1
    for a, b in zip(words, words[1:]):
        feats[f"b:{a} {b}"] += 1
    for w in words:
        padded = f" {w} "
        for n in (3, 4):
            for i in range(len(padded) - n + 1):
                feats["c:" + padded[i:i + n]] += 1
    return feats


class IntentModel:
    def __init__(self, texts, labels):
        self.labels = list(labels)
        docs = [_features(t) for t in texts]
        n = len(docs)
        df = Counter()
        for d in docs:
            df.update(d.keys())
        self.idf = {f: math.log((1 + n) / (1 + c)) + 1 for f, c in df.items()}
        self.default_idf = math.log(1 + n) + 1   # for features never seen in training
        self.vectors = [self._vectorise(d) for d in docs]

    def _vectorise(self, feats):
        vec = {f: (1 + math.log(c)) * self.idf.get(f, self.default_idf)
               for f, c in feats.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {f: v / norm for f, v in vec.items()}

    def predict(self, text):
        """Returns (intent, similarity 0..1) of the closest training phrase."""
        q = self._vectorise(_features(text))
        best = {}
        for vec, label in zip(self.vectors, self.labels):
            sim = sum(w * vec.get(f, 0.0) for f, w in q.items())
            if sim > best.get(label, 0.0):
                best[label] = sim
        if not best:
            return "fallback", 0.0
        label = max(best, key=best.get)
        return label, best[label]


def build_model(texts, labels):
    return IntentModel(texts, labels)


def train_classifier():
    global _model
    texts, labels = [], []
    for intent, phrases in load_phrases().items():
        for p in phrases:
            texts.append(p)
            labels.append(intent)
    _model = build_model(texts, labels)
    return _model


def classify(text: str):
    """Returns (intent, confidence).
    intent is a trained intent, 'sensitive_request' or 'fallback'."""
    if is_sensitive(text):          # rules run FIRST, whatever the model says
        return "sensitive_request", 1.0
    if _model is None:
        train_classifier()
    intent, conf = _model.predict(text)
    cleaned = prepare(text)
    if intent == "out_of_scope" or conf < CONFIDENCE_THRESHOLD:
        # a bare ID with no other words is still useful
        if "tktid" in cleaned:
            return "ticket_status", conf
        if "ordid" in cleaned:
            return "order_status", conf
        return "fallback", conf
    return intent, conf


if __name__ == "__main__":
    print("Type a message (empty line to quit)")
    while True:
        msg = input("> ").strip()
        if not msg:
            break
        print(classify(msg))