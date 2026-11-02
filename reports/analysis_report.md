# Customer Feedback Analysis Report

**Project:** AI-Powered Customer Feedback Analysis and Management Platform
**Course:** SOA Programming and Microservices (24SDCS03)
**Dataset:** `data/sample_feedback.csv` — 300 feedback entries across 8 products

---

## 1. Overview

This report summarizes the output of the platform's analytics pipeline
after running the full sample dataset through `sentiment_service` and
aggregating the results with `analytics_service`. Charts referenced below
are in `results/`.

## 2. Overall sentiment mix

| Sentiment | Count | % of total |
|---|---|---|
| Positive | 155 | 51.7% |
| Negative | 85 | 28.3% |
| Neutral | 60 | 20.0% |

Average star rating across all feedback: **3.40 / 5**.

See `results/sentiment_distribution.png` and `results/rating_by_sentiment.png`.

## 3. Product-level findings

Average rating by product, lowest to highest:

| Product | Avg. Rating |
|---|---|
| Payment Gateway | 3.08 |
| Subscription Plan | 3.11 |
| Mobile App | 3.23 |
| Web Portal | 3.34 |
| Loyalty Program | 3.38 |
| Delivery Service | 3.40 |
| Checkout Flow | 3.68 |
| Customer Support | 3.76 |

**Payment Gateway** and **Subscription Plan** are the two lowest-rated
products and are the best candidates for the product team to investigate
first. See `results/product_sentiment_heatmap.png` for the full
product × sentiment volume breakdown.

## 4. Negative-feedback alerting

Every feedback entry classified as `negative` is automatically forwarded
by `feedback_service` to `notification_service`, which logs a
severity-tagged alert (`HIGH` for 1–2 star ratings, `MEDIUM` otherwise).
This turns raw feedback into an actionable queue for support/product
teams instead of a static dataset someone has to manually re-read.

## 5. Model performance

The sentiment classifier (TF-IDF + Logistic Regression) reaches perfect
scores on the held-out test split — see `results/model_evaluation.md` for
the full breakdown and an important caveat about the synthetic dataset's
separability. The architecture — not this specific accuracy number — is
the reusable deliverable: pointing `train_model.py` at a real labeled
feedback export (e.g., from a support ticketing system) is a drop-in
replacement.

## 6. Recommendations

1. Prioritize a UX/reliability review of the **Payment Gateway** flow —
   it has both the lowest average rating and a high negative-sentiment
   share.
2. Route `HIGH` severity alerts (rating ≤ 2) to an on-call/support queue
   with an SLA, since these represent customers most likely to churn.
3. Re-train `sentiment_service` periodically on real (not templated)
   feedback text to keep the model calibrated to actual customer language.
