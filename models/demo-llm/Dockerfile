FROM python:3.11-slim

LABEL maintainer="Cirruslabs MLOps Team"
LABEL service="demo-llm"
LABEL model="demo-llm-v1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Create directories for models and data
RUN mkdir -p models data logs

# Create non-root user
RUN adduser --disabled-password --gecos '' modeluser && \
    chown -R modeluser:modeluser /app
USER modeluser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command (can be overridden)
CMD ["python", "-m", "uvicorn", "src.inference_service:app", "--host", "0.0.0.0", "--port", "8000"]