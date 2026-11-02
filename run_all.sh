#!/usr/bin/env bash
# run_all.sh
# ----------
# Reproduces every result in this project from a clean checkout, in order:
#   1. (Re)generate the sample dataset
#   2. Train the proposed ML sentiment model
#   3. Generate result charts + model evaluation report
#   4. Run the traditional-vs-proposed comparison (the "overcomes the
#      traditional model" evidence: results/baseline_vs_proposed.png
#      and results/baseline_comparison_report.md)
#
# Usage:
#   chmod +x run_all.sh   (first time only, Mac/Linux)
#   ./run_all.sh
#
# Or just run the four python commands manually — this script does nothing
# you couldn't do yourself, it only saves typing.

set -e  # stop immediately if any step fails

echo "=============================================="
echo " 1/4  Generating sample dataset"
echo "=============================================="
python3 data/generate_dataset.py

echo
echo "=============================================="
echo " 2/4  Training proposed model (TF-IDF + LogReg)"
echo "=============================================="
python3 src/sentiment_service/train_model.py

echo
echo "=============================================="
echo " 3/4  Generating result charts"
echo "=============================================="
python3 results/generate_results.py

echo
echo "=============================================="
echo " 4/4  Traditional vs. Proposed comparison"
echo "=============================================="
python3 results/baseline_comparison.py

echo
echo "=============================================="
echo " All done. Key outputs:"
echo "   results/model_evaluation.md"
echo "   results/baseline_comparison_report.md"
echo "   results/baseline_vs_proposed.png"
echo "   results/sentiment_distribution.png"
echo "=============================================="
echo
echo "To start the live microservices (5 separate terminals, from this folder):"
echo "   python3 src/sentiment_service/app.py"
echo "   python3 src/notification_service/app.py"
echo "   python3 src/feedback_service/app.py"
echo "   python3 src/analytics_service/app.py"
echo "   python3 src/api_gateway/app.py"
echo "Then: curl http://localhost:5000/health"
