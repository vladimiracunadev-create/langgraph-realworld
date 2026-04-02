FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Data directory defaults to internal if not provided
ENV DATA_DIR=/app/data
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8002"]
