FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY topology_mutator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY streaming/ ./streaming/
COPY configs/ ./configs/
COPY topology_mutator/ .

EXPOSE 8004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "1", "--log-level", "info"]
