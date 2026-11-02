"""
feedback_service
-----------------
Owns customer feedback data end-to-end (database-per-service pattern).
On every new submission it calls sentiment_service synchronously to
tag the feedback, and — if the sentiment is negative — notifies
notification_service so a human can follow up.

Endpoints:
    GET    /health
    POST   /feedback              body: {customer_name, product, feedback_text, rating}
    GET    /feedback              -> list all feedback
    GET    /feedback/<id>         -> single feedback item
    GET    /feedback/product/<p>  -> feedback filtered by product
"""

import os
import sqlite3
import requests
from datetime import datetime
from flask import Flask, request, jsonify, g

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "feedback.db")

SENTIMENT_SERVICE_URL = os.environ.get("SENTIMENT_SERVICE_URL", "http://localhost:5002")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5004")

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            product TEXT NOT NULL,
            feedback_text TEXT NOT NULL,
            rating INTEGER NOT NULL,
            sentiment TEXT,
            confidence REAL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "feedback_service", "status": "ok"})


@app.route("/feedback", methods=["POST"])
def create_feedback():
    payload = request.get_json(silent=True) or {}
    required = ["customer_name", "product", "feedback_text", "rating"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    sentiment, confidence = None, None
    try:
        resp = requests.post(
            f"{SENTIMENT_SERVICE_URL}/analyze",
            json={"text": payload["feedback_text"]},
            timeout=5,
        )
        if resp.ok:
            data = resp.json()
            sentiment = data.get("sentiment")
            confidence = data.get("confidence")
    except requests.RequestException:
        pass  # graceful degradation: still store the feedback even if sentiment_service is down

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    cur = db.execute(
        "INSERT INTO feedback (customer_name, product, feedback_text, rating, sentiment, confidence, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (payload["customer_name"], payload["product"], payload["feedback_text"],
         payload["rating"], sentiment, confidence, timestamp),
    )
    db.commit()
    new_id = cur.lastrowid

    if sentiment == "negative":
        try:
            requests.post(
                f"{NOTIFICATION_SERVICE_URL}/notify",
                json={
                    "feedback_id": new_id,
                    "customer_name": payload["customer_name"],
                    "product": payload["product"],
                    "feedback_text": payload["feedback_text"],
                    "rating": payload["rating"],
                },
                timeout=5,
            )
        except requests.RequestException:
            pass

    return jsonify({
        "id": new_id,
        "customer_name": payload["customer_name"],
        "product": payload["product"],
        "feedback_text": payload["feedback_text"],
        "rating": payload["rating"],
        "sentiment": sentiment,
        "confidence": confidence,
        "timestamp": timestamp,
    }), 201


@app.route("/feedback", methods=["GET"])
def list_feedback():
    db = get_db()
    rows = db.execute("SELECT * FROM feedback ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/feedback/<int:feedback_id>", methods=["GET"])
def get_feedback(feedback_id):
    db = get_db()
    row = db.execute("SELECT * FROM feedback WHERE id = ?", (feedback_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))


@app.route("/feedback/product/<product>", methods=["GET"])
def get_feedback_by_product(product):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM feedback WHERE product = ? ORDER BY id DESC", (product,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=False)
