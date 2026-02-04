FROM python:3.11.10-slim

# Security Hardening: don't run as root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
      && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# App
COPY src /app/src
COPY web /app/web

# Default data location
RUN mkdir -p /app/data && chown -p appuser:appuser /app/data
ENV DATA_DIR=/app/data

USER appuser

EXPOSE 8009

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8009/health || exit 1

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8009"]

