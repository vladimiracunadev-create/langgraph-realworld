FROM python:3.11-slim

WORKDIR /app

# Instalar curl para healthchecks y herramientas de build si fuera necesario
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear directorio de datos si no existe (aunque se montará como volumen)
RUN mkdir -p /app/data

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8013

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8013"]
