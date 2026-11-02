# AI-Powered Customer Feedback Analysis and Management Platform

**Course:** SOA Programming and Microservices (24SDCS03)
**Team:** M. Bharath (2420030380) · Mani Teja (2420030139) · K. Dikshith (2420030607)
**Institution:** Koneru Lakshmaiah Education Foundation, Deemed to be University (Off Campus, Hyderabad, Bachupally)

A microservices-based platform that collects customer feedback, automatically
classifies its sentiment using a trained ML model, raises alerts on negative
feedback, and surfaces aggregate analytics — demonstrating core SOA patterns
(service decomposition, database-per-service, API gateway, graceful
degradation) on top of a real AI component.

---

## Folder structure

```
.
├── README.md
├── requirements.txt
├── docker-compose.yml
├── run_all.sh                  # one command reproduces every result below
├── data/
│   ├── generate_dataset.py     # creates the sample dataset
│   └── sample_feedback.csv     # 300 synthetic feedback rows across 8 products
├── docs/
│   ├── architecture.md         # service breakdown + diagram
│   ├── api_documentation.md    # every endpoint, request/response shapes
│   └── setup_guide.md          # local + Docker run instructions
├── reports/
│   └── analysis_report.md      # written findings from the sample dataset
├── results/
│   ├── generate_results.py     # regenerates the charts below
│   ├── baseline_comparison.py  # traditional vs. proposed model benchmark
│   ├── metrics.json            # raw proposed-model metrics
│   ├── model_evaluation.md     # readable proposed-model evaluation
│   ├── baseline_comparison.json        # raw traditional-vs-proposed metrics
│   ├── baseline_comparison_report.md   # readable traditional-vs-proposed writeup
│   ├── baseline_vs_proposed.png        # comparison chart
│   ├── sentiment_distribution.png
│   ├── rating_by_sentiment.png
│   └── product_sentiment_heatmap.png
└── src/
    ├── api_gateway/            # public entry point (port 5000)
    ├── feedback_service/       # feedback CRUD + SQLite (port 5001)
    ├── sentiment_service/      # TF-IDF + Logistic Regression classifier (port 5002)
    ├── analytics_service/      # aggregation/reporting (port 5003)
    └── notification_service/   # negative-feedback alerting (port 5004)
```

## Architecture at a glance

```
Client → API Gateway (5000) → feedback_service (5001) ──► sentiment_service (5002)
                              │                        └─► notification_service (5004) [if negative]
                              └─────────────────────────► analytics_service (5003) reads feedback_service
```

Full write-up, including why the services are split this way, is in
[`docs/architecture.md`](docs/architecture.md).

## Quick start

**Easiest: one command reproduces everything**
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
./run_all.sh
```
This regenerates the dataset, trains the model, builds every chart, and runs
the traditional-vs-proposed comparison in one go. See what it prints for the
exact list of files it produces.

**Or run each step yourself:**
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python data/generate_dataset.py                 # (already generated, but reproducible)
python src/sentiment_service/train_model.py      # trains the proposed ML model
python results/generate_results.py               # generates charts + eval report
python results/baseline_comparison.py             # traditional vs. proposed comparison

# in 5 terminals, from the project root:
python src/sentiment_service/app.py
python src/notification_service/app.py
python src/feedback_service/app.py
python src/analytics_service/app.py
python src/api_gateway/app.py

curl http://localhost:5000/health
```

Or with Docker: `docker compose up --build`. Full instructions in
[`docs/setup_guide.md`](docs/setup_guide.md).

## Try it

```bash
curl -X POST http://localhost:5000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"A. Rao","product":"Mobile App","feedback_text":"The app keeps crashing on checkout.","rating":1}'

curl http://localhost:5000/api/analytics/summary
```

Full endpoint reference: [`docs/api_documentation.md`](docs/api_documentation.md).

## Key results (on the included sample dataset, 300 entries)

| Sentiment | Share |
|---|---|
| Positive | 51.7% |
| Negative | 28.3% |
| Neutral | 20.0% |

Lowest-rated product: **Payment Gateway** (avg. 3.08 / 5). Full analysis in
[`reports/analysis_report.md`](reports/analysis_report.md); model metrics in
[`results/model_evaluation.md`](results/model_evaluation.md).

## Proposed model vs. the traditional approach

`results/baseline_comparison.py` benchmarks the proposed model (TF-IDF +
Logistic Regression) against a traditional keyword/lexicon rule engine —
the standard pre-ML approach to feedback sentiment tagging — on the exact
same held-out test split:

| Metric | Traditional (rules) | Proposed (ML) |
|---|---|---|
| Accuracy | 83.3% | 100.0% |
| Precision | 85.9% | 100.0% |
| Recall | 83.3% | 100.0% |
| F1-score | 83.8% | 100.0% |

Full write-up (including *why* the ML model wins, not just the numbers) in
[`results/baseline_comparison_report.md`](results/baseline_comparison_report.md);
chart in `results/baseline_vs_proposed.png`.

## Tech stack

Python · Flask (REST microservices) · scikit-learn (TF-IDF + Logistic
Regression) · SQLite · pandas · matplotlib · Docker / Docker Compose
