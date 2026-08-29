# RecoverOS & AI Revenue Recovery Agent Dockerfile
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt /app/requirements.txt
COPY backend/requirements.txt /app/backend_requirements.txt

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r backend_requirements.txt || true && \
    pip install --no-cache-dir fastapi uvicorn pydantic sqlalchemy anthropic

# Copy application source code
COPY . /app

# Generate synthetic payment dataset and train ML recovery model
RUN python3 data/generate_data.py && python3 models/train_model.py

# Expose Streamlit (8501) and FastAPI (8000) ports
EXPOSE 8501 8000

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
