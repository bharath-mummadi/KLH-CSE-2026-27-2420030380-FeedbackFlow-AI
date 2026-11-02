FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/analytics_service/ ./src/analytics_service/
COPY data/ ./data/

EXPOSE 5003

CMD ["python", "src/analytics_service/app.py"]
