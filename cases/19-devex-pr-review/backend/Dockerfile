FROM python:3.11-slim

# Security Hardening: don't run as root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# System deps (minimal)
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
        curl \
      && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# App
COPY src /app/src

# Default data location
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data
ENV PR_DATA_PATH=/app/data/sample_pr.json

USER appuser

EXPOSE 8019

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8019/health || exit 1

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8019"]
