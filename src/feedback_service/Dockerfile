FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/feedback_service/ ./src/feedback_service/
COPY data/ ./data/

EXPOSE 5001

CMD ["python", "src/feedback_service/app.py"]
