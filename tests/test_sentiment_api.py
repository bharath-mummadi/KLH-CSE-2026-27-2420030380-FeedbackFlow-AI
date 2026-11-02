from src.analytics_service.app import _infer_problem
from src.sentiment_service.app import app


def test_sentiment_accepts_feedback_text_field():
    client = app.test_client()

    response = client.post(
        "/analyze",
        json={
            "feedback_text": "The checkout is ridiculously slow and keeps freezing."
        },
    )

    assert response.status_code == 200, response.get_data(as_text=True)
    payload = response.get_json()
    assert payload["sentiment"] in {"positive", "neutral", "negative"}


def test_negative_product_quality_comment_is_classified_negative():
    client = app.test_client()

    response = client.post(
        "/analyze",
        json={
            "feedback_text": "The TV is not nice, the image is not up to the mark and also i got the damaged box which means it is not handled carefully."
        },
    )

    assert response.status_code == 200, response.get_data(as_text=True)
    payload = response.get_json()
    assert payload["sentiment"] == "negative", payload


def test_issue_classifier_maps_common_feedback_topics():
    assert _infer_problem("The TV is not nice, the image is not up to the mark and the box was damaged") == "quality"
    assert _infer_problem("The package was delivered late and the box was damaged") == "delivery"
    assert _infer_problem("I was charged twice for the order and payment failed") == "payment"


def test_laptop_bug_comment_is_classified_negative():
    client = app.test_client()

    response = client.post(
        "/analyze",
        json={
            "feedback_text": "There are so many bugs in my laptop and it is not working properly."
        },
    )

    assert response.status_code == 200, response.get_data(as_text=True)
    payload = response.get_json()
    assert payload["sentiment"] == "negative", payload


def test_gateway_homepage_returns_html():
    from src.api_gateway.app import app as gateway_app

    client = gateway_app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert "Customer Feedback Intelligence" in response.get_data(as_text=True)
