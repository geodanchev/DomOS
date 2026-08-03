# DomOS Cashier MVP - Backend Dockerfile
FROM python:3.13-slim

# Build arguments for versioning
ARG GIT_COMMIT_SHA=""

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    GIT_COMMIT_SHA=${GIT_COMMIT_SHA}

# Set work directory
WORKDIR /app

# Install system dependencies (including fonts for PDF generation with Cyrillic support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Cache buster - invalidates cache when commit SHA changes
# This ensures entrypoint.sh and other app files are always fresh
ARG CACHEBUST=1

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose port (Cloud Run uses PORT env variable, default 8080)
EXPOSE 8080

# Note: Cloud Run has its own health check probes, no need for HEALTHCHECK instruction
# The startup probe checks if the container is listening on PORT

# Use entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
