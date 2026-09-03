FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PostgreSQL and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

ENV PYTHONPATH=/app

# Railway injects $PORT dynamically
CMD sh -c "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
