# Use Python 3.10 as the base image
FROM python:3.10-slim

# Build arguments
ARG IMAGE_VERSION=unknown
ARG DEV_STATE=PROD
ARG FLASK_ENV=production
ARG DEBUG=false

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    FLASK_ENV=${FLASK_ENV} \
    DEV_STATE=${DEV_STATE} \
    DEBUG=${DEBUG} \
    IMAGE_VERSION=${IMAGE_VERSION} \
    FLASK_APP=run.py \
    PORT=${PORT:-5000}

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    python3-dev \
    libc6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project
COPY . .

# Add entrypoint script
COPY scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create a non-root user and switch to it
RUN addgroup --system appgroup && \
    adduser --system --group appuser && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port for Flask app
EXPOSE 5000

# Run the application through entrypoint script
CMD ["bash", "/app/scripts/entrypoint.sh"]
