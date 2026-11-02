"""
generate_results.py
--------------------
Loads data/sample_feedback.csv, runs every row through the trained
sentiment model directly (no need for the services to be running),
and produces the charts + evaluation artifacts saved in this folder:

    - sentiment_distribution.png
    - rating_by_sentiment.png
    - product_sentiment_heatmap.png
    - model_evaluation.md   (human-readable version of metrics.json)

Run from the project root:
    python results/generate_results.py
"""

import os
import json
import joblib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA_PATH = os.path.join(ROOT, "data", "sample_feedback.csv")
SENTIMENT_DIR = os.path.join(ROOT, "src", "sentiment_service")

COLORS = {"positive": "#2E7D32", "neutral": "#F9A825", "negative": "#C62828"}


def main():
    df = pd.read_csv(DATA_PATH)

    model = joblib.load(os.path.join(SENTIMENT_DIR, "model.pkl"))
    vectorizer = joblib.load(os.path.join(SENTIMENT_DIR, "vectorizer.pkl"))
    df["predicted_sentiment"] = model.predict(vectorizer.transform(df["feedback_text"]))

    # --- Chart 1: overall sentiment distribution ---
    counts = df["predicted_sentiment"].value_counts().reindex(["positive", "neutral", "negative"]).fillna(0)
    plt.figure(figsize=(6, 4))
    plt.bar(counts.index, counts.values, color=[COLORS[s] for s in counts.index])
    plt.title("Overall Feedback Sentiment Distribution")
    plt.ylabel("Number of Feedback Entries")
    for i, v in enumerate(counts.values):
        plt.text(i, v + 2, str(int(v)), ha="center")
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "sentiment_distribution.png"), dpi=150)
    plt.close()

    # --- Chart 2: average rating by sentiment (sanity check) ---
    avg_rating = df.groupby("predicted_sentiment")["rating"].mean().reindex(["positive", "neutral", "negative"])
    plt.figure(figsize=(6, 4))
    plt.bar(avg_rating.index, avg_rating.values, color=[COLORS[s] for s in avg_rating.index])
    plt.title("Average Star Rating by Predicted Sentiment")
    plt.ylabel("Average Rating (1-5)")
    plt.ylim(0, 5.5)
    for i, v in enumerate(avg_rating.values):
        plt.text(i, v + 0.1, f"{v:.2f}", ha="center")
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "rating_by_sentiment.png"), dpi=150)
    plt.close()

    # --- Chart 3: product x sentiment heatmap ---
    pivot = pd.crosstab(df["product"], df["predicted_sentiment"]).reindex(columns=["positive", "neutral", "negative"], fill_value=0)
    plt.figure(figsize=(7, 5))
    im = plt.imshow(pivot.values, cmap="RdYlGn_r", aspect="auto")
    plt.xticks(range(len(pivot.columns)), pivot.columns)
    plt.yticks(range(len(pivot.index)), pivot.index)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            plt.text(j, i, pivot.values[i, j], ha="center", va="center", color="black")
    plt.title("Feedback Volume by Product and Sentiment")
    plt.colorbar(im, label="Number of Feedback Entries")
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "product_sentiment_heatmap.png"), dpi=150)
    plt.close()

    # --- model_evaluation.md from metrics.json (written by train_model.py) ---
    metrics_path = os.path.join(HERE, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            m = json.load(f)

        labels = m["labels"]
        cm = m["confusion_matrix"]
        cm_header = "| actual \\ predicted | " + " | ".join(labels) + " |"
        cm_sep = "|---" * (len(labels) + 1) + "|"
        cm_rows = "\n".join(
            "| **" + labels[i] + "** | " + " | ".join(str(v) for v in row) + " |"
            for i, row in enumerate(cm)
        )

        md = f"""# Sentiment Model Evaluation

Model: TF-IDF (unigrams + bigrams, 2000 features) + Logistic Regression (`class_weight="balanced"`)
Train/test split: {m['train_size']} train / {m['test_size']} test (80/20, stratified by sentiment)

## Metrics (weighted average across classes)

| Metric | Score |
|---|---|
| Accuracy | {m['accuracy']} |
| Precision | {m['precision_weighted']} |
| Recall | {m['recall_weighted']} |
| F1-score | {m['f1_weighted']} |

## Confusion Matrix

{cm_header}
{cm_sep}
{cm_rows}

## Note on scores

The dataset used here is generated from a fixed set of sentence templates
(see `data/generate_dataset.py`), which makes the classes highly separable
and pushes accuracy close to 1.0. On real, unstructured customer feedback
the same pipeline would score lower — the architecture (not the specific
numbers) is the deliverable: swap in a real labeled feedback dataset and
re-run `train_model.py` to get representative metrics.
"""
        with open(os.path.join(HERE, "model_evaluation.md"), "w") as f:
            f.write(md)

    print("Results generated:")
    print(" - sentiment_distribution.png")
    print(" - rating_by_sentiment.png")
    print(" - product_sentiment_heatmap.png")
    print(" - model_evaluation.md")


if __name__ == "__main__":
    main()
