"""
generate_dataset.py
--------------------
Creates data/sample_feedback.csv — a synthetic but realistic customer
feedback dataset used to train the sentiment model and to demo the
analytics/reporting pipeline.

Run:
    python generate_dataset.py
"""

import csv
import os
import random
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(ROOT, "sample_feedback.csv")

random.seed(42)

PRODUCTS = [
    "Mobile App", "Web Portal", "Payment Gateway", "Customer Support",
    "Subscription Plan", "Delivery Service", "Loyalty Program", "Checkout Flow",
]

POSITIVE_TEMPLATES = [
    "The {p} is fantastic, everything works smoothly and quickly.",
    "I love using the {p}, it saved me so much time.",
    "Great experience with the {p}, very intuitive and reliable.",
    "The {p} exceeded my expectations, will recommend to friends.",
    "Excellent {p}! Fast, clean, and easy to use.",
    "Really happy with the {p}, support team was helpful too.",
    "The new update to the {p} fixed all my issues, works perfectly now.",
    "Impressed by how reliable the {p} has been over the past month.",
    "The laptop runs smoothly and the display quality is excellent.",
    "Delivery was on time and the product quality was great.",
    "Very satisfied with the purchase, the service was fast and helpful.",
    "The product is amazing, easy to use, and works perfectly.",
    "The battery life is excellent and the laptop performs really well.",
]

NEUTRAL_TEMPLATES = [
    "The {p} works fine, nothing special but does the job.",
    "The {p} is okay, could use a few more features.",
    "Average experience with the {p}, some parts felt slow.",
    "The {p} is decent, but the design feels a bit outdated.",
    "Not bad, not great — the {p} just does the bare minimum.",
    "The laptop is acceptable, though the performance is average.",
    "Delivery was okay, but the package arrived a bit late.",
    "The product functions normally but the interface feels average.",
    "It works, but I expected better quality for the price.",
]

NEGATIVE_TEMPLATES = [
    "The {p} keeps crashing, very frustrating experience.",
    "Terrible support from the {p}, no one responded for days.",
    "The {p} is slow and unreliable, I want a refund.",
    "I'm disappointed with the {p}, it never works as advertised.",
    "The {p} has too many bugs, unusable most of the time.",
    "Worst experience ever with the {p}, switching to a competitor.",
    "The {p} charged me twice and support was unhelpful.",
    "Extremely poor performance from the {p}, needs urgent fixing.",
    "There are so many bugs in my laptop and it is not working properly.",
    "The TV quality is poor, the image is not up to the mark and the box was damaged.",
    "The delivery was late and the product arrived damaged.",
    "I was charged twice for the order and the payment failed unexpectedly.",
    "The laptop is broken, the screen flickers, and it keeps freezing.",
    "The package was not handled carefully and arrived damaged.",
    "The quality is very poor and the item is not worth the money.",
    "I am unhappy with the service, the product is defective and support is slow.",
]

CUSTOMER_NAMES = [
    "A. Rao", "S. Mehta", "J. Kumar", "P. Singh", "R. Das", "N. Iyer",
    "T. Sharma", "K. Reddy", "V. Nair", "M. Ghosh", "L. Verma", "D. Pillai",
    "H. Bose", "C. Menon", "F. Joshi", "B. Chatterjee",
]


def make_row(idx, start_date):
    bucket = random.choices(["pos", "neu", "neg"], weights=[0.5, 0.2, 0.3])[0]
    product = random.choice(PRODUCTS)

    if bucket == "pos":
        text = random.choice(POSITIVE_TEMPLATES).format(p=product)
        rating = random.choice([4, 5, 5])
        sentiment = "positive"
    elif bucket == "neu":
        text = random.choice(NEUTRAL_TEMPLATES).format(p=product)
        rating = 3
        sentiment = "neutral"
    else:
        text = random.choice(NEGATIVE_TEMPLATES).format(p=product)
        rating = random.choice([1, 1, 2])
        sentiment = "negative"

    date = start_date + timedelta(days=random.randint(0, 89))

    return {
        "feedback_id": idx,
        "customer_name": random.choice(CUSTOMER_NAMES),
        "product": product,
        "feedback_text": text,
        "rating": rating,
        "sentiment": sentiment,
        "timestamp": date.strftime("%Y-%m-%d"),
    }


def main(n=300):
    start_date = datetime(2026, 5, 1)
    rows = [make_row(i, start_date) for i in range(1, n + 1)]
    rows.sort(key=lambda r: r["timestamp"])

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "feedback_id", "customer_name", "product", "feedback_text",
                "rating", "sentiment", "timestamp",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
