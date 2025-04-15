# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py

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

# Add startup script 
COPY scripts/docker_startup.sh /app/docker_startup.sh
RUN chmod +x /app/docker_startup.sh

# Create a non-root user and switch to it
RUN addgroup --system appgroup && \
    adduser --system --group appuser && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Use the startup script when DEV_STATE=TEST, otherwise use gunicorn directly
CMD ["/bin/bash", "-c", "if [ \"$DEV_STATE\" = \"TEST\" ]; then /app/docker_startup.sh; else gunicorn --bind 0.0.0.0:5000 --workers 4 run:app; fi"]