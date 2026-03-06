FROM python:3.11-slim

WORKDIR /app

# Instalar curl para healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root user (seguridad)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8010

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8010"]
