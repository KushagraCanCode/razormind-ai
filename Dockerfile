# Multi-stage Dockerfile for RazorMind AI
FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Generate data and train initial model artifacts
RUN python data/generate_data.py && \
    python database/init_db.py && \
    python notebooks/generate_notebooks.py

EXPOSE 8000 8501

# Default command launches FastAPI backend which serves the interactive dashboard
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
