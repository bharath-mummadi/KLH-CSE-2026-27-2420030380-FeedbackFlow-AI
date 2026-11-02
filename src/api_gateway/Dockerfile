FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/api_gateway/ ./src/api_gateway/
COPY data/ ./data/

EXPOSE 5000

CMD ["python", "src/api_gateway/app.py"]
