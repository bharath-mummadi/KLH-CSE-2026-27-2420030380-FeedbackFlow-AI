# Sentiment Model Evaluation

Model: TF-IDF (unigrams + bigrams, 2000 features) + Logistic Regression (`class_weight="balanced"`)
Train/test split: 240 train / 60 test (80/20, stratified by sentiment)

## Metrics (weighted average across classes)

| Metric | Score |
|---|---|
| Accuracy | 1.0 |
| Precision | 1.0 |
| Recall | 1.0 |
| F1-score | 1.0 |

## Confusion Matrix

| actual \ predicted | negative | neutral | positive |
|---|---|---|---|
| **negative** | 16 | 0 | 0 |
| **neutral** | 0 | 12 | 0 |
| **positive** | 0 | 0 | 32 |

## Note on scores

The dataset used here is generated from a fixed set of sentence templates
(see `data/generate_dataset.py`), which makes the classes highly separable
and pushes accuracy close to 1.0. On real, unstructured customer feedback
the same pipeline would score lower — the architecture (not the specific
numbers) is the deliverable: swap in a real labeled feedback dataset and
re-run `train_model.py` to get representative metrics.
