# Setup Guide

## Option A — Run locally with Python (recommended for grading/demo)

**Fastest path:** after installing dependencies (step 1), just run
`./run_all.sh` — it does steps 2–4 below in one go and prints exactly
what it produced. The instructions below are the same steps done by hand,
in case you want to run or re-run any one of them individually.

### 1. Create a virtual environment and install dependencies
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate the sample dataset (already included, but regenerable)
```bash
python data/generate_dataset.py
```

### 3. Train the sentiment model
```bash
python src/sentiment_service/train_model.py
```
This writes `src/sentiment_service/model.pkl`, `vectorizer.pkl`, and
`results/metrics.json`.

### 4. Generate charts / evaluation report
```bash
python results/generate_results.py
```

### 5. Benchmark against the traditional (rule-based) approach
```bash
python results/baseline_comparison.py
```
This trains nothing new — it evaluates a hand-written keyword/lexicon
classifier (the "traditional model") and the proposed ML model
(step 3) on the same held-out test split, and writes
`results/baseline_comparison_report.md`, `results/baseline_comparison.json`,
and `results/baseline_vs_proposed.png`.

### 6. Start every microservice
Open five terminals (or use `&` to background each) from the project root:
```bash
python src/sentiment_service/app.py      # port 5002
python src/notification_service/app.py   # port 5004
python src/feedback_service/app.py       # port 5001
python src/analytics_service/app.py      # port 5003
python src/api_gateway/app.py            # port 5000
```

### 7. Try it
```bash
curl http://localhost:5000/health

curl -X POST http://localhost:5000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"A. Rao","product":"Mobile App","feedback_text":"App keeps crashing on checkout.","rating":1}'

curl http://localhost:5000/api/analytics/summary
```

---

## Option B — Run with Docker Compose

```bash
docker compose up --build
```
This builds and starts all five services on the same ports as above,
wired together via the `FEEDBACK_SERVICE_URL` / `SENTIMENT_SERVICE_URL` /
etc. environment variables defined in `docker-compose.yml`. Stop with
`docker compose down`.

> Note: the sentiment model must be trained (Option A, step 3) before
> building the `sentiment_service` image, since `model.pkl` /
> `vectorizer.pkl` are copied into the image.

---

## Project layout
```
data/       sample dataset + generator script
docs/       architecture, API reference, this guide
reports/    written analysis report
results/    generated charts, trained-model metrics
src/        the five microservices
```
