FROM python:3.11-slim

WORKDIR /app

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends         curl       && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# App
COPY src /app/src
COPY web /app/web

# Default data location (override via env DATA_DIR=/app/data)
RUN mkdir -p /app/data
ENV DATA_DIR=/app/data

EXPOSE 8009

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8009"]
