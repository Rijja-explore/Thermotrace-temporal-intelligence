FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install lightweight PyTorch CPU wheel first for fast Docker builds
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY apps/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

ENV PYTHONPATH=/app:/app/services/temporal_intelligence:/app/services/classification
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn apps.backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

