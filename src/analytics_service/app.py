"""
analytics_service
------------------
Reads from feedback_service's data and produces aggregate insights —
kept as its own service so heavy reporting/query load never impacts
the write-path (feedback_service) or the ML path (sentiment_service).

Endpoints:
    GET /health
    GET /analytics/summary          -> overall counts, avg rating, sentiment split
    GET /analytics/by-product       -> per-product breakdown
"""

import os
import re
import requests
from collections import Counter, defaultdict
from flask import Flask, jsonify

FEEDBACK_SERVICE_URL = os.environ.get("FEEDBACK_SERVICE_URL", "http://localhost:5001")

app = Flask(__name__)

ISSUE_PATTERNS = {
    "delivery": ["delivery", "delivered late", "late delivery", "shipment", "missing", "package", "arrived late", "box damaged", "damaged box", "not handled carefully", "shipping"],
    "quality": ["quality", "image", "screen", "pixel", "damaged", "damage", "not nice", "not up to the mark", "poor quality", "defective", "broken"],
    "payment": ["payment", "charged", "billing", "refund", "double", "charge", "card", "checkout", "transaction", "invoice"],
    "slow": ["slow", "lag", "delay", "performance", "timeout"],
    "crash": ["crash", "crashes", "freeze", "freezing", "stuck"],
    "support": ["support", "response", "unhelpful", "ignored", "agent"],
    "bug": ["bug", "bugs", "error", "errors", "fail"],
    "design": ["design", "outdated", "confusing", "layout", "interface"],
    "subscription": ["subscription", "plan", "pricing", "renewal", "cost"],
}


def _fetch_all_feedback():
    resp = requests.get(f"{FEEDBACK_SERVICE_URL}/feedback", timeout=5)
    resp.raise_for_status()
    return resp.json()


def _infer_problem(text):
    cleaned = re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    for issue, keywords in ISSUE_PATTERNS.items():
        if any(keyword in cleaned for keyword in keywords):
            return issue

    words = re.findall(r"\b[a-z]+\b", cleaned)
    return Counter(words).most_common(1)[0][0] if words else "general"


def _product_issue_summary(rows):
    product_problems = defaultdict(list)
    for r in rows:
        if (r.get("sentiment") or "").lower() == "negative":
            product_problems[r.get("product", "Unknown")].append(r.get("feedback_text", ""))

    result = {}
    for product, texts in product_problems.items():
        counts = Counter(_infer_problem(text) for text in texts)
        most_common = counts.most_common(1)[0] if counts else ("general", 0)
        result[product] = {
            "most_common_problem": most_common[0],
            "negative_count": len(texts),
            "issue_breakdown": dict(counts),
        }
    return result


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "analytics_service", "status": "ok"})


@app.route("/analytics/summary", methods=["GET"])
def summary():
    try:
        rows = _fetch_all_feedback()
    except requests.RequestException as e:
        return jsonify({"error": f"feedback_service unavailable: {e}"}), 502

    if not rows:
        return jsonify({"total_feedback": 0, "product_problem_summary": {}})

    total = len(rows)
    avg_rating = round(sum(r["rating"] for r in rows) / total, 2)
    sentiment_counts = defaultdict(int)
    for r in rows:
        sentiment_counts[r.get("sentiment") or "unlabeled"] += 1

    return jsonify({
        "total_feedback": total,
        "average_rating": avg_rating,
        "sentiment_breakdown": dict(sentiment_counts),
        "sentiment_breakdown_pct": {
            k: round(v / total * 100, 1) for k, v in sentiment_counts.items()
        },
        "product_problem_summary": _product_issue_summary(rows),
    })


@app.route("/analytics/by-product", methods=["GET"])
def by_product():
    try:
        rows = _fetch_all_feedback()
    except requests.RequestException as e:
        return jsonify({"error": f"feedback_service unavailable: {e}"}), 502

    grouped = defaultdict(lambda: {"count": 0, "rating_sum": 0, "sentiment": defaultdict(int), "negative_texts": []})
    for r in rows:
        g = grouped[r["product"]]
        g["count"] += 1
        g["rating_sum"] += r["rating"]
        g["sentiment"][r.get("sentiment") or "unlabeled"] += 1
        if (r.get("sentiment") or "").lower() == "negative":
            g["negative_texts"].append(r.get("feedback_text", ""))

    result = {}
    for product, g in grouped.items():
        issue_counts = Counter(_infer_problem(text) for text in g["negative_texts"])
        most_common = issue_counts.most_common(1)[0] if issue_counts else ("general", 0)
        result[product] = {
            "count": g["count"],
            "average_rating": round(g["rating_sum"] / g["count"], 2),
            "sentiment_breakdown": dict(g["sentiment"]),
            "most_common_problem": most_common[0],
            "negative_count": len(g["negative_texts"]),
        }

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)
