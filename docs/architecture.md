# Architecture — AI-Powered Customer Feedback Analysis and Management Platform

## 1. Style: Service-Oriented Architecture / Microservices

The platform is decomposed into five independent, single-responsibility
services that communicate over synchronous REST/HTTP (JSON). Each service
owns its own data and can be developed, deployed, scaled, and restarted
independently — the core promise of SOA/microservices.

```
                        ┌────────────────────┐
                Client  │                    │
              ─────────►│    API Gateway     │  (port 5000)
                        │  src/api_gateway   │
                        └─────────┬──────────┘
                                  │  routes requests
           ┌──────────────┬──────┴───────┬──────────────────┐
           ▼              ▼              ▼                  ▼
  ┌─────────────────┐ ┌───────────────┐ ┌──────────────────┐ ┌───────────────────┐
  │ feedback_service │ │sentiment_svc  │ │ analytics_service │ │notification_service│
  │   (port 5001)    │ │  (port 5002)  │ │    (port 5003)    │ │    (port 5004)     │
  │ SQLite DB        │ │ TF-IDF + LR   │ │ reads from        │ │ notifications.log  │
  │ (feedback.db)    │ │ model.pkl     │ │ feedback_service   │ │                    │
  └────────┬─────────┘ └───────────────┘ └──────────────────┘ └─────────┬──────────┘
           │  calls on every new submission ─────────────────────────────┘
           │  (sentiment tagging, then negative-feedback alert)
           ▼
   stores tagged feedback
```

## 2. Services

| Service | Responsibility | Data store | Port |
|---|---|---|---|
| **api_gateway** | Single public entry point; routes/aggregates calls to internal services so clients never talk to internals directly | none (stateless) | 5000 |
| **feedback_service** | Owns feedback CRUD; on create, calls `sentiment_service` to tag sentiment, then calls `notification_service` if the result is negative | SQLite (`feedback.db`) | 5001 |
| **sentiment_service** | Pure ML inference: text in, sentiment label + confidence out. No knowledge of feedback storage | model artifacts (`model.pkl`, `vectorizer.pkl`) | 5002 |
| **analytics_service** | Aggregates/summarizes feedback (overall + per-product breakdowns) by querying `feedback_service` | none (stateless, queries feedback_service) | 5003 |
| **notification_service** | Durable event log for negative-feedback alerts | flat log (`notifications.log`) | 5004 |

## 3. Why split it this way

- **Database-per-service**: `feedback_service` is the only service that touches
  `feedback.db`. No other service reads/writes it directly — they always go
  through `feedback_service`'s API. This avoids the classic shared-database
  anti-pattern and keeps services independently deployable.
- **Single Responsibility**: `sentiment_service` does nothing but classify
  text. It can be swapped for a different model, scaled independently (it's
  the most CPU-hungry service), or replaced with a hosted LLM without
  touching any other service.
- **Graceful degradation**: `feedback_service` still stores a feedback
  entry even if `sentiment_service` or `notification_service` are
  unreachable — sentiment/alerting are treated as best-effort enrichments,
  not hard dependencies, which is a standard resiliency pattern in SOA.
- **API Gateway pattern**: clients only need to know one address
  (`api_gateway`). Internal service URLs are configured via environment
  variables (`FEEDBACK_SERVICE_URL`, `SENTIMENT_SERVICE_URL`, etc.), so
  services can move hosts/ports without breaking clients.

## 4. Communication

All inter-service calls are synchronous REST over HTTP using JSON payloads
(implemented with Python's `requests` library). This keeps the reference
implementation simple to run and grade; the same service boundaries would
work unchanged if some calls were later moved to an async message broker
(e.g., RabbitMQ/Kafka) for the notification flow.

## 5. Deployment

`docker-compose.yml` at the project root defines one container per service
so the whole platform can be brought up with a single command
(`docker compose up --build`). See `docs/setup_guide.md`.
