"""
train_model.py
---------------
Trains a TF-IDF + Logistic Regression sentiment classifier on
data/sample_feedback.csv and saves the fitted vectorizer + model
so the Flask sentiment_service can load them at request time.

Run from the project root:
    python src/sentiment_service/train_model.py
"""

import os
import json
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, classification_report,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA_PATH = os.path.join(ROOT, "data", "sample_feedback.csv")
MODEL_PATH = os.path.join(HERE, "model.pkl")
VECTORIZER_PATH = os.path.join(HERE, "vectorizer.pkl")
RESULTS_DIR = os.path.join(ROOT, "results")


def main():
    df = pd.read_csv(DATA_PATH)

    X_train, X_test, y_train, y_test = train_test_split(
        df["feedback_text"], df["sentiment"],
        test_size=0.2, random_state=42, stratify=df["sentiment"],
    )

    vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), stop_words="english")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)

    acc = accuracy_score(y_test, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="weighted", zero_division=0
    )
    labels = sorted(df["sentiment"].unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    report = classification_report(y_test, y_pred, zero_division=0)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    metrics = {
        "accuracy": round(acc, 4),
        "precision_weighted": round(precision, 4),
        "recall_weighted": round(recall, 4),
        "f1_weighted": round(f1, 4),
        "labels": labels,
        "confusion_matrix": cm.tolist(),
        "test_size": len(y_test),
        "train_size": len(y_train),
    }
    with open(os.path.join(RESULTS_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print("Training complete.")
    print(f"Accuracy: {acc:.4f} | Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f}")
    print("\nClassification report:\n", report)
    print(f"Model saved to:      {MODEL_PATH}")
    print(f"Vectorizer saved to: {VECTORIZER_PATH}")
    print(f"Metrics saved to:    {os.path.join(RESULTS_DIR, 'metrics.json')}")


if __name__ == "__main__":
    main()
