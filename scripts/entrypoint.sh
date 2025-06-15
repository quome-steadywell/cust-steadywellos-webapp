#!/bin/bash
# entrypoint.sh - Container entrypoint script for both development and production

# Exit on any error
set -e

echo "=== PALLIATIVE CARE PLATFORM STARTUP LOG $(date) ==="
echo "Container starting with hostname: $(hostname)"
echo "Environment: DEV_STATE=${DEV_STATE:-unset}"

# In production (/app is read-only), use /tmp for logs
# In development, we can write to /app
if [ "${DEV_STATE:-TEST}" = "PROD" ]; then
    echo "Production mode: Using /tmp for writable files"
    mkdir -p /tmp/logs
    LOG_FILE="/tmp/startup.log"
    # Create symlink for backward compatibility if it doesn't exist
    if [ ! -L "/app/logs" ] && [ ! -d "/app/logs" ]; then
        ln -s /tmp/logs /app/logs 2>/dev/null || true
    fi
else
    echo "Development mode: Using /app for logs"
    LOG_FILE="/app/startup_log.txt"
fi

# Start with a fresh log file
echo "=== STARTUP LOG $(date) ===" > "$LOG_FILE"

# For production, write logs to both stdout and log file
# For development, can use the log file
if [ "${DEV_STATE:-TEST}" = "PROD" ]; then
    # In production, just output to stdout/stderr for Docker logging
    echo "Logging to stdout/stderr for Docker logs"
else
    # In development, also log to file
    exec > >(tee -a "$LOG_FILE") 2>&1
fi

echo "Starting Palliative Care Platform..."

# Wait for database to be ready
echo "Waiting for database to be available..."

# Determine database connection details based on environment
if [ "${DEV_STATE:-TEST}" = "PROD" ]; then
    # Production mode - use remote database or DATABASE_URL
    if [ -n "$DATABASE_URL" ]; then
        echo "Using DATABASE_URL for production connection"
        DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*://[^@]*@\([^:]*\):.*|\1|p')
        DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*://[^@]*@[^:]*:\([0-9]*\)/.*|\1|p')
        DB_USER=$(echo "$DATABASE_URL" | sed -n 's|.*://\([^:]*\):.*@.*|\1|p')
        DB_HOST=${DB_HOST:-"localhost"}
        DB_PORT=${DB_PORT:-"5432"}
        DB_USER=${DB_USER:-"postgres"}
    else
        DB_HOST=${POSTGRES_REMOTE_HOST:-"localhost"}
        DB_PORT=${POSTGRES_REMOTE_PORT:-"5432"}
        DB_USER=${POSTGRES_REMOTE_USER:-"postgres"}
    fi
else
    # Development mode - use local database
    DB_HOST=${POSTGRES_LOCAL_HOST:-"db"}
    DB_PORT=${POSTGRES_LOCAL_PORT:-"5432"}
    DB_USER=${POSTGRES_LOCAL_USER:-"postgres"}
fi

echo "Database connection details:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"

# Try to connect to Postgres for up to 60 seconds (12 tries, 5 seconds each)
RETRIES=12
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" || [ $RETRIES -eq 0 ]; do
  echo "Waiting for postgres server to be ready, $((RETRIES--)) remaining attempts..."
  sleep 5
done

if [ $RETRIES -eq 0 ]; then
    echo "❌ Failed to connect to PostgreSQL after 60 seconds"
    echo "Connection details used:"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  User: $DB_USER"
    exit 1
fi

echo "✅ PostgreSQL is ready at $DB_HOST:$DB_PORT!"

# Database initialization is handled by the Flask application itself
# The app will check and initialize the database on startup
echo "Database initialization will be handled by the Flask application"

# Start the application
echo "Starting Flask application..."
if [ "${DEV_STATE:-TEST}" = "PROD" ]; then
    echo "Production mode: Starting with Gunicorn"
    # Use PORT environment variable, fallback to 5000 if not set
    APP_PORT=${PORT:-5000}
    echo "Starting Gunicorn on port: $APP_PORT"
    exec gunicorn --bind 0.0.0.0:$APP_PORT --workers 4 --access-logfile="-" --error-logfile="-" run:app
else
    echo "Development mode: This should not run in development (Flask dev server is used instead)"
    echo "If you see this, run with: docker-compose -f docker-compose-dev.yml up"
    exit 1
fi
