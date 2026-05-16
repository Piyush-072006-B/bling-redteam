FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

COPY topology_generator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared layers
COPY streaming/ ./streaming/
COPY configs/ ./configs/

# Copy service code
COPY topology_generator/ .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1", "--log-level", "info"]
