FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/sentiment_service/ ./src/sentiment_service/
COPY data/ ./data/

EXPOSE 5002

CMD ["python", "src/sentiment_service/app.py"]
