"""
baseline_comparison.py
------------------------
Implements the TRADITIONAL approach to feedback sentiment classification —
a manual keyword/lexicon-matching rule engine, the kind of method used
before ML-based classifiers — and benchmarks it head-to-head against the
PROPOSED system's model (TF-IDF + Logistic Regression, src/sentiment_service)
on the exact same held-out test split.

This produces the evidence for the "proposed system overcomes the
traditional model" claim: same data, same split, two methods, one report.

Run from the project root:
    python results/baseline_comparison.py
"""

import os
import json
import re
import joblib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, confusion_matrix,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA_PATH = os.path.join(ROOT, "data", "sample_feedback.csv")
SENTIMENT_DIR = os.path.join(ROOT, "src", "sentiment_service")

# ---------------------------------------------------------------------------
# TRADITIONAL MODEL: keyword / lexicon rule engine
# ---------------------------------------------------------------------------
# This is representative of the "traditional" approach used before ML-based
# text classifiers: a fixed, hand-written list of positive/negative words,
# with sentiment decided purely by which list has more matches. It has no
# training phase and cannot learn context, negation, phrasing, or domain
# vocabulary it wasn't explicitly given.

POSITIVE_WORDS = {
    "great", "good", "love", "loved", "excellent", "fantastic", "happy",
    "smooth", "fast", "reliable", "easy", "impressed", "recommend",
    "perfect", "amazing", "helpful", "quick", "clean", "intuitive",
    "exceeded",
}

NEGATIVE_WORDS = {
    "bad", "terrible", "worst", "slow", "crash", "crashing", "crashes",
    "bug", "bugs", "unreliable", "frustrating", "disappointed", "poor",
    "unusable", "refund", "unhelpful", "never", "charged", "twice",
    "urgent", "awful",
}


def traditional_predict(text: str) -> str:
    words = set(re.findall(r"[a-zA-Z']+", text.lower()))
    pos_hits = len(words & POSITIVE_WORDS)
    neg_hits = len(words & NEGATIVE_WORDS)
    if pos_hits > neg_hits:
        return "positive"
    if neg_hits > pos_hits:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# PROPOSED MODEL: TF-IDF + Logistic Regression (already trained)
# ---------------------------------------------------------------------------

def load_proposed_model():
    model_path = os.path.join(SENTIMENT_DIR, "model.pkl")
    vectorizer_path = os.path.join(SENTIMENT_DIR, "vectorizer.pkl")
    if not (os.path.exists(model_path) and os.path.exists(vectorizer_path)):
        raise RuntimeError(
            "Proposed model not found. Run `python src/sentiment_service/train_model.py` first."
        )
    return joblib.load(model_path), joblib.load(vectorizer_path)


def evaluate(y_true, y_pred, labels):
    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0, labels=labels
    )
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return {
        "accuracy": round(acc, 4),
        "precision_weighted": round(precision, 4),
        "recall_weighted": round(recall, 4),
        "f1_weighted": round(f1, 4),
        "confusion_matrix": cm.tolist(),
    }


def main():
    df = pd.read_csv(DATA_PATH)
    labels = sorted(df["sentiment"].unique())

    # Same split used to train/evaluate the proposed model, for a fair comparison
    _, X_test, _, y_test = train_test_split(
        df["feedback_text"], df["sentiment"],
        test_size=0.2, random_state=42, stratify=df["sentiment"],
    )

    # --- Traditional model predictions ---
    y_pred_traditional = X_test.apply(traditional_predict)
    traditional_metrics = evaluate(y_test, y_pred_traditional, labels)

    # --- Proposed model predictions ---
    model, vectorizer = load_proposed_model()
    y_pred_proposed = model.predict(vectorizer.transform(X_test))
    proposed_metrics = evaluate(y_test, y_pred_proposed, labels)

    # --- Save comparison JSON ---
    comparison = {
        "test_size": len(y_test),
        "labels": labels,
        "traditional_model": {
            "name": "Keyword/Lexicon Rule Engine",
            **traditional_metrics,
        },
        "proposed_model": {
            "name": "TF-IDF + Logistic Regression",
            **proposed_metrics,
        },
    }
    with open(os.path.join(HERE, "baseline_comparison.json"), "w") as f:
        json.dump(comparison, f, indent=2)

    # --- Chart: side-by-side metric comparison ---
    metric_names = ["accuracy", "precision_weighted", "recall_weighted", "f1_weighted"]
    metric_labels = ["Accuracy", "Precision", "Recall", "F1-score"]
    traditional_vals = [traditional_metrics[m] * 100 for m in metric_names]
    proposed_vals = [proposed_metrics[m] * 100 for m in metric_names]

    x = range(len(metric_names))
    width = 0.35

    plt.figure(figsize=(8, 5))
    bars1 = plt.bar([i - width/2 for i in x], traditional_vals, width,
                     label="Traditional (keyword rules)", color="#9E9E9E")
    bars2 = plt.bar([i + width/2 for i in x], proposed_vals, width,
                     label="Proposed (TF-IDF + LogReg)", color="#C00000")

    for bars in (bars1, bars2):
        for b in bars:
            plt.text(b.get_x() + b.get_width()/2, b.get_height() + 1,
                      f"{b.get_height():.0f}%", ha="center", fontsize=9)

    plt.xticks(list(x), metric_labels)
    plt.ylabel("Score (%)")
    plt.ylim(0, 115)
    plt.title("Traditional vs. Proposed Sentiment Model — Same Test Set")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "baseline_vs_proposed.png"), dpi=150)
    plt.close()

    # --- Markdown report ---
    md = f"""# Traditional vs. Proposed Model — Comparison Report

Both models were evaluated on the **same held-out test split**
({comparison['test_size']} rows, 80/20 split, `random_state=42`,
stratified by sentiment) from `data/sample_feedback.csv`.

## Traditional model: keyword / lexicon rule engine

A fixed, hand-written positive/negative word list (see `POSITIVE_WORDS`
and `NEGATIVE_WORDS` in this script). Sentiment is whichever list has
more matches in the text. This mirrors the traditional, pre-ML approach
to feedback classification: no training phase, no context awareness,
no handling of negation or domain-specific phrasing beyond what's
hand-listed.

## Proposed model: TF-IDF + Logistic Regression

Learns weighted patterns (unigrams + bigrams) directly from labeled
feedback text (`src/sentiment_service/train_model.py`), so it adapts to
the actual vocabulary and phrasing in the data instead of a fixed list.

## Results

| Metric | Traditional (rules) | Proposed (ML) | Improvement |
|---|---|---|---|
| Accuracy | {traditional_metrics['accuracy']*100:.1f}% | {proposed_metrics['accuracy']*100:.1f}% | {(proposed_metrics['accuracy']-traditional_metrics['accuracy'])*100:+.1f} pts |
| Precision (weighted) | {traditional_metrics['precision_weighted']*100:.1f}% | {proposed_metrics['precision_weighted']*100:.1f}% | {(proposed_metrics['precision_weighted']-traditional_metrics['precision_weighted'])*100:+.1f} pts |
| Recall (weighted) | {traditional_metrics['recall_weighted']*100:.1f}% | {proposed_metrics['recall_weighted']*100:.1f}% | {(proposed_metrics['recall_weighted']-traditional_metrics['recall_weighted'])*100:+.1f} pts |
| F1-score (weighted) | {traditional_metrics['f1_weighted']*100:.1f}% | {proposed_metrics['f1_weighted']*100:.1f}% | {(proposed_metrics['f1_weighted']-traditional_metrics['f1_weighted'])*100:+.1f} pts |

See `baseline_vs_proposed.png` for the chart and `baseline_comparison.json`
for the raw numbers (including both confusion matrices).

## Why the proposed model wins

- **Learns from data** instead of relying on a fixed word list someone
  has to maintain by hand — it picks up product-specific and domain
  phrasing the lexicon never anticipated.
- **Handles multi-word patterns** (bigrams) like "not working" or
  "highly recommend", not just isolated keywords.
- **Produces a confidence score** per prediction (via `predict_proba`),
  which the lexicon approach cannot — useful for routing low-confidence
  cases to human review.
- **Improves with more data.** Feeding it more labeled feedback and
  re-running `train_model.py` improves accuracy; the keyword list only
  improves if someone manually edits it.
"""
    with open(os.path.join(HERE, "baseline_comparison_report.md"), "w") as f:
        f.write(md)

    print("Comparison complete.")
    print(f"Traditional  — Accuracy: {traditional_metrics['accuracy']:.4f}  F1: {traditional_metrics['f1_weighted']:.4f}")
    print(f"Proposed     — Accuracy: {proposed_metrics['accuracy']:.4f}  F1: {proposed_metrics['f1_weighted']:.4f}")
    print(f"\nSaved: baseline_comparison.json, baseline_vs_proposed.png, baseline_comparison_report.md")


if __name__ == "__main__":
    main()
