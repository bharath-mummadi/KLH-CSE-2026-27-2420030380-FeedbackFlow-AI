"""
api_gateway
-----------
Single public entry point for the whole platform (API Gateway pattern).
Clients (web/mobile) only ever talk to this service; it fans requests
out to the internal microservices, so internal service addresses,
ports, and implementations can change freely without breaking clients.

Endpoints (client-facing):
    GET  /health                     -> health of the gateway + all downstream services
    GET  /                           -> dashboard UI for the project
    POST /api/feedback               -> proxies to feedback_service
    GET  /api/feedback               -> proxies to feedback_service
    GET  /api/feedback/<id>          -> proxies to feedback_service
    GET  /api/analytics/summary      -> proxies to analytics_service
    GET  /api/analytics/by-product   -> proxies to analytics_service
    POST /api/sentiment              -> proxies to sentiment_service (direct analyze, no storage)
    GET  /api/alerts                 -> proxies to notification_service
"""

import os
import requests
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

SERVICES = {
    "feedback": os.environ.get("FEEDBACK_SERVICE_URL", "http://localhost:5001"),
    "sentiment": os.environ.get("SENTIMENT_SERVICE_URL", "http://localhost:5002"),
    "analytics": os.environ.get("ANALYTICS_SERVICE_URL", "http://localhost:5003"),
    "notification": os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5004"),
}

HTML_PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Customer Feedback Intelligence</title>
    <style>
      :root {
        --bg: #0b1020;
        --panel: rgba(15, 23, 42, 0.8);
        --card: rgba(15, 23, 42, 0.9);
        --primary: #7c3aed;
        --primary-2: #22c55e;
        --warning: #f59e0b;
        --text: #e2e8f0;
        --muted: #94a3b8;
        --danger: #ef4444;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Arial, Helvetica, sans-serif;
        background: linear-gradient(135deg, #0f172a, #111827 30%, #1e1b4b);
        color: var(--text);
      }
      .container {
        max-width: 1280px; margin: 0 auto; padding: 32px 20px 60px;
      }
      .topbar {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 24px;
      }
      .brand {
        font-size: 1.85rem; font-weight: 800; letter-spacing: 0.04em;
      }
      .status-pill {
        background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34,197,94,0.4);
        color: #bbf7d0; padding: 8px 16px; border-radius: 999px; font-size: 0.9rem;
      }
      .layout {
        display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 22px;
      }
      .stack {
        display: flex; flex-direction: column; gap: 22px;
      }
      .card {
        background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(148,163,184,0.16);
        border-radius: 18px; box-shadow: 0 12px 32px rgba(0,0,0,0.2);
        padding: 22px;
      }
      .card h3 {
        margin: 0 0 18px; font-size: 1.1rem; color: #f8fafc;
      }
      label {
        display: block; color: #dbeafe; margin-bottom: 8px; font-weight: 600;
      }
      input, textarea, button {
        width: 100%; border-radius: 12px; border: 1px solid rgba(148,163,184,0.22);
        background: rgba(15, 23, 42, 0.9); color: var(--text); padding: 12px 14px;
        font-size: 1rem; margin-bottom: 14px;
      }
      textarea { min-height: 140px; resize: vertical; }
      button {
        cursor: pointer; border: none; background: linear-gradient(135deg, #8b5cf6, #7c3aed);
        font-weight: 700; margin-top: 6px; transition: transform 0.2s ease;
      }
      button:hover { transform: translateY(-1px); }
      .stats {
        display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px;
      }
      .metric {
        background: linear-gradient(180deg, rgba(124,58,237,0.12), rgba(30,41,59,0.8));
        border: 1px solid rgba(124,58,237,0.26); border-radius: 14px;
        padding: 16px 10px; text-align: center;
      }
      .metric small { display: block; color: var(--muted); margin-bottom: 6px; }
      .metric strong { font-size: 1.35rem; }
      .sentiment-box {
        margin-top: 14px; padding: 18px; border-radius: 14px;
        background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.38);
      }
      .sentiment-box.error {
        background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.35);
      }
      .alerts, .issue-list, .history-list { list-style: none; padding: 0; margin: 0; }
      .alerts li, .issue-list li, .history-item {
        background: rgba(30,41,59,0.8); border: 1px solid rgba(148,163,184,0.12);
        border-radius: 12px; padding: 12px; margin-bottom: 10px;
      }
      .issue-list li strong { color: #f8fafc; }
      .history-item {
        display: flex; flex-direction: column; gap: 8px;
      }
      .history-header {
        display: flex; justify-content: space-between; align-items: center; gap: 12px;
      }
      .history-item p {
        margin: 0; color: #e2e8f0; line-height: 1.5;
      }
      .history-item small {
        color: var(--muted);
      }
      .badge {
        display: inline-block; padding: 5px 9px; border-radius: 999px; font-size: 0.75rem; font-weight: 700;
        text-transform: capitalize;
      }
      .badge.positive { background: rgba(34,197,94,0.14); color: #bbf7d0; }
      .badge.negative { background: rgba(239,68,68,0.12); color: #fecaca; }
      .badge.neutral { background: rgba(245,158,11,0.12); color: #fde68a; }
      .hidden { display: none; }
      @media (max-width: 980px) {
        .layout { grid-template-columns: 1fr; }
        .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="topbar">
        <div class="brand">Customer Feedback Intelligence</div>
        <div class="status-pill" id="systemStatus">System online</div>
      </div>

      <div class="layout">
        <div class="stack">
          <div class="card">
            <h3>Submit feedback</h3>
            <form id="feedbackForm">
              <label>Customer name</label>
              <input name="customer_name" placeholder="John Doe" required />

              <label>Product</label>
              <input name="product" placeholder="Enter product name" required />

              <label>Rating</label>
              <input name="rating" type="number" min="1" max="5" step="1" placeholder="Enter 1 to 5" required />

              <label>Feedback</label>
              <textarea name="feedback_text" placeholder="Tell us what went well or what needs improvement..." required></textarea>

              <button type="submit">Analyze feedback</button>
            </form>

            <div id="resultBox" class="sentiment-box hidden"></div>
          </div>
        </div>

        <div class="stack">
          <div class="card">
            <h3>Overall sentiment</h3>
            <div class="stats">
              <div class="metric"><small>Total</small><strong id="totalFeedback">0</strong></div>
              <div class="metric"><small>Positive</small><strong id="positiveCount">0</strong></div>
              <div class="metric"><small>Negative</small><strong id="negativeCount">0</strong></div>
              <div class="metric"><small>Neutral</small><strong id="neutralCount">0</strong></div>
              <div class="metric"><small>Avg rating</small><strong id="avgRating">0</strong></div>
            </div>
          </div>

          <div class="card">
            <h3>Most common product problem</h3>
            <ul id="issueList" class="issue-list"></ul>
          </div>

          <div class="card">
            <h3>Recent alerts</h3>
            <ul id="alertsList" class="alerts"></ul>
          </div>
        </div>
      </div>

      <div class="card" style="margin-top: 22px;">
        <h3>Previous feedback reports</h3>
        <ul id="historyList" class="history-list"></ul>
      </div>
    </div>

    <script>
      function renderIssueList(data) {
        const list = document.getElementById('issueList');
        const summary = data.product_problem_summary || {};
        const entries = Object.entries(summary);
        list.innerHTML = '';

        if (!entries.length) {
          list.innerHTML = '<li>No negative product issues yet.</li>';
          return;
        }

        entries.slice(0, 5).forEach(([product, issue]) => {
          const li = document.createElement('li');
          li.innerHTML = `<strong>${product}</strong>: ${issue.most_common_problem} (${issue.negative_count} complaints)`;
          list.appendChild(li);
        });
      }

      async function fetchSummary() {
        try {
          const response = await fetch('/api/analytics/summary');
          const data = await response.json();
          document.getElementById('totalFeedback').textContent = data.total_feedback || 0;
          document.getElementById('avgRating').textContent = data.average_rating || 0;

          const sentimentBreakdown = data.sentiment_breakdown || {};
          document.getElementById('positiveCount').textContent = sentimentBreakdown.positive || 0;
          document.getElementById('negativeCount').textContent = sentimentBreakdown.negative || 0;
          document.getElementById('neutralCount').textContent = sentimentBreakdown.neutral || 0;

          renderIssueList(data);
        } catch (err) {
          document.getElementById('systemStatus').textContent = 'Analytics unavailable';
        }
      }

      async function fetchAlerts() {
        try {
          const response = await fetch('/api/alerts');
          const data = await response.json();
          const list = document.getElementById('alertsList');
          list.innerHTML = '';
          if (!Array.isArray(data) || data.length === 0) {
            list.innerHTML = '<li>No recent alerts.</li>';
            return;
          }
          data.slice(-5).reverse().forEach(alert => {
            const li = document.createElement('li');
            li.textContent = `${alert.product}: ${alert.customer_name} — ${alert.feedback_text}`;
            list.appendChild(li);
          });
        } catch (err) {
          document.getElementById('alertsList').innerHTML = '<li>Alerts service unreachable.</li>';
        }
      }

      async function fetchFeedbackHistory() {
        try {
          const response = await fetch('/api/feedback');
          const data = await response.json();
          const list = document.getElementById('historyList');
          list.innerHTML = '';
          if (!Array.isArray(data) || data.length === 0) {
            list.innerHTML = '<li>No feedback items yet.</li>';
            return;
          }
          data.slice(0, 8).forEach(item => {
            const row = document.createElement('li');
            row.className = 'history-item';
            row.innerHTML = `
              <div class="history-header">
                <span>${item.product}</span>
                <span class="badge ${item.sentiment || 'neutral'}">${item.sentiment || 'neutral'}</span>
              </div>
              <p>${item.feedback_text}</p>
              <small>Rating: ${item.rating} • ${item.customer_name}</small>
            `;
            list.appendChild(row);
          });
        } catch (err) {
          document.getElementById('historyList').innerHTML = '<li>Unable to load feedback history.</li>';
        }
      }

      document.getElementById('feedbackForm').addEventListener('submit', async function (event) {
        event.preventDefault();
        const form = event.currentTarget;
        const payload = {
          customer_name: form.customer_name.value,
          product: form.product.value,
          rating: Number(form.rating.value),
          feedback_text: form.feedback_text.value
        };

        const resultBox = document.getElementById('resultBox');
        resultBox.classList.remove('hidden', 'error');
        resultBox.innerHTML = 'Analyzing your feedback...';

        try {
          const res = await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          const data = await res.json();

          if (!res.ok) {
            throw new Error(data.error || 'Submission failed');
          }

          resultBox.innerHTML = `
            <strong>Sentiment:</strong> ${data.sentiment || 'unknown'}<br>
            <strong>Confidence:</strong> ${(data.confidence || 0) * 100}%<br>
            <strong>Saved:</strong> feedback ID ${data.id}
          `;
          if ((data.sentiment || '').toLowerCase() === 'negative') {
            resultBox.classList.add('error');
          }
          fetchSummary();
          fetchAlerts();
          fetchFeedbackHistory();
          form.reset();
        } catch (error) {
          resultBox.classList.add('error');
          resultBox.innerHTML = `Submission error: ${error.message}`;
        }
      });

      fetchSummary();
      fetchAlerts();
      fetchFeedbackHistory();
    </script>
  </body>
</html>
"""


def _proxy(method, service, path, **kwargs):
    url = f"{SERVICES[service]}{path}"
    try:
        resp = requests.request(method, url, timeout=8, **kwargs)
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        return jsonify({"error": f"{service} service unreachable: {e}"}), 502


@app.route("/", methods=["GET"])
def home():
    return Response(HTML_PAGE, mimetype="text/html")


@app.route("/health", methods=["GET"])
def health():
    statuses = {"gateway": "ok"}
    for name, base_url in SERVICES.items():
        try:
            r = requests.get(f"{base_url}/health", timeout=3)
            statuses[name] = "ok" if r.ok else f"error ({r.status_code})"
        except requests.RequestException:
            statuses[name] = "unreachable"
    return jsonify(statuses)


@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    return _proxy("POST", "feedback", "/feedback", json=request.get_json(silent=True))


@app.route("/api/feedback", methods=["GET"])
def list_feedback():
    return _proxy("GET", "feedback", "/feedback")


@app.route("/api/feedback/<int:feedback_id>", methods=["GET"])
def get_feedback(feedback_id):
    return _proxy("GET", "feedback", f"/feedback/{feedback_id}")


@app.route("/api/feedback/", methods=["GET", "POST"])
def feedback_alias():
    if request.method == "GET":
        return list_feedback()
    return submit_feedback()


@app.route("/api/analytics/summary", methods=["GET"])
def analytics_summary():
    return _proxy("GET", "analytics", "/analytics/summary")


@app.route("/api/analytics/by-product", methods=["GET"])
def analytics_by_product():
    return _proxy("GET", "analytics", "/analytics/by-product")


@app.route("/api/sentiment", methods=["POST"])
@app.route("/api/sentiment/", methods=["POST"])
def sentiment():
    payload = request.get_json(silent=True) or {}
    if "text" not in payload and "feedback_text" not in payload:
        payload = {"text": payload.get("text") or payload.get("feedback_text") or ""}
    return _proxy("POST", "sentiment", "/analyze", json=payload)


@app.route("/api/analyze", methods=["POST"])
def analyze_alias():
    return sentiment()


@app.route("/api/alerts", methods=["GET"])
def alerts():
    return _proxy("GET", "notification", "/alerts")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
