"""
sentiment_service
------------------
Microservice responsible for ONE thing only (single-responsibility,
as expected of a service in an SOA / microservices design): given a
piece of feedback text, return its sentiment.

Endpoints:
    GET  /health
    POST /analyze        body: {"text": "..."}  -> {"sentiment", "confidence", "scores"}
"""

import os
import re
import joblib
from flask import Flask, request, jsonify

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "model.pkl")
VECTORIZER_PATH = os.path.join(HERE, "vectorizer.pkl")

POSITIVE_WORDS = {
    "excellent", "great", "love", "amazing", "helpful", "fast", "easy",
    "smooth", "smoothly", "reliable", "happy", "perfect", "quick", "good",
    "friendly", "satisfied", "awesome", "impressed", "nice"
}
NEGATIVE_WORDS = {
    "bad", "terrible", "slow", "crash", "crashes", "bug", "bugs",
    "frustrating", "unusable", "poor", "broken", "error", "errors",
    "issue", "issues", "slowly", "worst", "hate", "refund", "wrong",
    "disappointed", "confusing", "unhelpful", "damaged", "damage", "defective",
    "carelessly", "careless", "unsafe", "cheap", "low", "blurred", "faulty"
}
NEUTRAL_WORDS = {"okay", "fine", "average", "decent", "normal", "standard", "works", "acceptable"}
NEGATION_WORDS = {"not", "never", "no", "isnt", "isn't", "wasnt", "wasn't", "dont", "don't", "doesnt", "doesn't", "cant", "can't", "cannot", "hardly"}
NEGATIVE_PATTERNS = {
    "damaged box",
    "not handled carefully",
    "not nice",
    "not up to the mark",
    "poor quality",
    "bad image",
    "damaged package",
    "not worth",
    "very poor",
    "not good",
    "image not clear",
    "quality is poor",
    "cheap quality",
    "not acceptable",
    "not working properly",
    "not working",
    "many bugs",
    "so many bugs",
    "bugs in my laptop",
    "buggy",
    "laptop is broken"
}

app = Flask(__name__)

_model = None
_vectorizer = None


def _normalize(text):
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()


def _rule_based_prediction(text):
    cleaned = _normalize(text)
    if not cleaned:
        return None, 0.0

    tokens = cleaned.split()
    pos_score = 0
    neg_score = 0
    neutral_score = 0

    for phrase in NEGATIVE_PATTERNS:
        if phrase in cleaned:
            neg_score += 2

    for i, token in enumerate(tokens):
        if token in NEGATION_WORDS and i + 1 < len(tokens):
            next_token = tokens[i + 1]
            if next_token in POSITIVE_WORDS:
                neg_score += 2
            if next_token in NEUTRAL_WORDS:
                neg_score += 1
            if next_token in {"working", "working properly"}:
                neg_score += 2
        if token in POSITIVE_WORDS:
            pos_score += 1
        if token in NEGATIVE_WORDS:
            neg_score += 1
        if token in NEUTRAL_WORDS:
            neutral_score += 1

    if any(token in {"bug", "bugs", "buggy", "broken"} for token in tokens):
        neg_score += 2
    if "not working" in cleaned or "not working properly" in cleaned:
        neg_score += 3

    if neg_score >= 1:
        return "negative", min(0.99, 0.72 + neg_score * 0.08)
    if pos_score > neg_score and pos_score >= 1:
        return "positive", min(0.98, 0.62 + pos_score * 0.08)
    if neutral_score > 0:
        return "neutral", 0.6
    return None, 0.0


def _load_artifacts():
    global _model, _vectorizer
    if _model is None or _vectorizer is None:
        if not (os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH)):
            raise RuntimeError(
                "Model artifacts not found. Run `python src/sentiment_service/train_model.py` first."
            )
        _model = joblib.load(MODEL_PATH)
        _vectorizer = joblib.load(VECTORIZER_PATH)
    return _model, _vectorizer


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "sentiment_service", "status": "ok"})


@app.route("/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or payload.get("feedback_text") or "").strip()

    if not text:
        return jsonify({"error": "Field 'text' or 'feedback_text' is required."}), 400

    rule_prediction, rule_confidence = _rule_based_prediction(text)
    model, vectorizer = _load_artifacts()
    vec = vectorizer.transform([text])

    prediction = model.predict(vec)[0]
    proba = model.predict_proba(vec)[0]
    scores = {label: round(float(p), 4) for label, p in zip(model.classes_, proba)}
    confidence = round(float(max(proba)), 4)

    if rule_prediction and (prediction != rule_prediction or confidence < 0.65):
        prediction = rule_prediction
        confidence = round(max(confidence, rule_confidence), 4)

    return jsonify({
        "text": text,
        "sentiment": prediction,
        "confidence": confidence,
        "scores": scores,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
