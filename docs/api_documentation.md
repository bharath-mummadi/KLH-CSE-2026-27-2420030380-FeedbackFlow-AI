# API Documentation

All requests/responses are JSON. Base URL for normal client use is the
**API Gateway**: `http://localhost:5000`. Internal service ports are also
listed below in case you want to call a service directly while developing.

---

## API Gateway (`http://localhost:5000`)

### `GET /health`
Returns gateway status plus a live health check of every downstream service.
```json
{"gateway":"ok","feedback":"ok","sentiment":"ok","analytics":"ok","notification":"ok"}
```

### `POST /api/feedback`
Submit new customer feedback. Proxies to `feedback_service`, which
synchronously tags sentiment and raises an alert if negative.

Request body:
```json
{
  "customer_name": "A. Rao",
  "product": "Mobile App",
  "feedback_text": "The app keeps crashing on checkout.",
  "rating": 1
}
```

Response `201`:
```json
{
  "id": 42,
  "customer_name": "A. Rao",
  "product": "Mobile App",
  "feedback_text": "The app keeps crashing on checkout.",
  "rating": 1,
  "sentiment": "negative",
  "confidence": 0.81,
  "timestamp": "2026-08-27 03:46:42"
}
```

### `GET /api/feedback`
Returns all stored feedback, newest first.

### `GET /api/feedback/<id>`
Returns a single feedback record, or `404` if not found.

### `GET /api/analytics/summary`
```json
{
  "total_feedback": 300,
  "average_rating": 3.57,
  "sentiment_breakdown": {"positive": 155, "neutral": 60, "negative": 85},
  "sentiment_breakdown_pct": {"positive": 51.7, "neutral": 20.0, "negative": 28.3}
}
```

### `GET /api/analytics/by-product`
Per-product breakdown of count / average rating / sentiment split.

### `POST /api/sentiment`
Direct sentiment check — does **not** store anything, just classifies text.
```json
{"text": "Great experience, very fast support!"}
```
```json
{"text":"...", "sentiment":"positive", "confidence":0.87,
 "scores":{"positive":0.87,"neutral":0.09,"negative":0.04}}
```

### `GET /api/alerts`
Returns every negative-feedback alert raised so far.

---

## Internal service endpoints (direct access, for debugging)

| Service | Base URL | Endpoints |
|---|---|---|
| feedback_service | `http://localhost:5001` | `GET /health`, `POST /feedback`, `GET /feedback`, `GET /feedback/<id>`, `GET /feedback/product/<product>` |
| sentiment_service | `http://localhost:5002` | `GET /health`, `POST /analyze` |
| analytics_service | `http://localhost:5003` | `GET /health`, `GET /analytics/summary`, `GET /analytics/by-product` |
| notification_service | `http://localhost:5004` | `GET /health`, `POST /notify`, `GET /alerts` |

All error responses follow the shape `{"error": "message"}` with an
appropriate 4xx/5xx status code.
