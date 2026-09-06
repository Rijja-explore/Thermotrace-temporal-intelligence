FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY apps/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    joblib scikit-learn pandas numpy pydantic pyyaml reportlab

COPY . /app/

ENV PYTHONPATH=/app:/app/services/temporal_intelligence:/app/services/classification

EXPOSE 8000

CMD ["uvicorn", "apps.backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
