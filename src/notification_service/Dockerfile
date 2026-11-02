FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/notification_service/ ./src/notification_service/
COPY data/ ./data/

EXPOSE 5004

CMD ["python", "src/notification_service/app.py"]
