"""
notification_service
---------------------
Small, single-purpose service that reacts to negative feedback events
raised by feedback_service. In production this would push to email /
Slack / SMS; here it durably logs the alert to notifications.log so
the workflow is demonstrable without external providers.

Endpoints:
    GET  /health
    POST /notify     body: {feedback_id, customer_name, product, feedback_text, rating}
    GET  /alerts      -> list all alerts raised so far
"""

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(HERE, "notifications.log")

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "notification_service", "status": "ok"})


@app.route("/notify", methods=["POST"])
def notify():
    payload = request.get_json(silent=True) or {}
    required = ["feedback_id", "customer_name", "product", "feedback_text", "rating"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    alert = {
        "alert_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "severity": "HIGH" if payload["rating"] <= 2 else "MEDIUM",
        **payload,
    }

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert) + "\n")

    return jsonify({"status": "alert_logged", "alert": alert}), 201


@app.route("/alerts", methods=["GET"])
def alerts():
    if not os.path.exists(LOG_PATH):
        return jsonify([])
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return jsonify(rows)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=False)
