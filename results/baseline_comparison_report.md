# Traditional vs. Proposed Model — Comparison Report

Both models were evaluated on the **same held-out test split**
(60 rows, 80/20 split, `random_state=42`,
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
| Accuracy | 88.3% | 100.0% | +11.7 pts |
| Precision (weighted) | 91.0% | 100.0% | +9.0 pts |
| Recall (weighted) | 88.3% | 100.0% | +11.7 pts |
| F1-score (weighted) | 89.0% | 100.0% | +11.0 pts |

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
