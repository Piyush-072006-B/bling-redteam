FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

COPY escape_analyzer/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY streaming/ ./streaming/
COPY configs/ ./configs/
COPY escape_analyzer/ .

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005", "--workers", "1", "--log-level", "info"]
