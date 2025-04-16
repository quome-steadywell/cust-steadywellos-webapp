#!/bin/bash
# docker_startup.sh - Production version of the startup script for Quome Cloud

# Save log output to a file that can be accessed by the web app
LOG_FILE="/app/startup_log.txt"

# Start with a fresh log file
echo "=== STARTUP LOG $(date) ===" > "$LOG_FILE"

# Redirect all output to the log file as well as console
exec > >(tee -a "$LOG_FILE") 2>&1

# Exit on any error
set -e

echo "Starting Palliative Care Platform..."

# Wait for database to be ready
echo "Waiting for database to be available..."
# Try to connect to Postgres for up to 60 seconds (12 tries, 5 seconds each)
RETRIES=12
until pg_isready -h ${POSTGRES_HOST:-db} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} || [ $RETRIES -eq 0 ]; do
  echo "Waiting for postgres server to be ready, $((RETRIES--)) remaining attempts..."
  sleep 5
done

# Initialize and seed database if in TEST mode
if [ "${DEV_STATE}" = "TEST" ]; then
  echo "DEV_STATE is set to TEST. Setting up test database..."
  
  # Check if backup file exists
  BACKUP_FILE="/app/data/backup/pallcare_db.sql"
  if [ -f "$BACKUP_FILE" ]; then
    echo "Found backup file. Setting up database from backup..."
    
    # Use the direct connection URL for Quome deployment
    echo "Setting up database using Quome Cloud connection..."
    
    # Use the PALLCARE_URL environment variable if available, fall back to constructed URL
    DB_URL="${PALLCARE_URL:-postgresql://cust-86880079-c52c-4e5f-9501-101f8a779c66.pallcare:ubcgvwXWWOliJ3NzA0lHNmnZQZoToF2r0TQxoP9wEhvkc1swrX6oHQiN9AVdSWdt@pallcare-cluster.databases:5432/pallcare}"
    
    echo "Using database connection: ${DB_URL}"
    
    # Drop database if exists
    PGPASSWORD="ubcgvwXWWOliJ3NzA0lHNmnZQZoToF2r0TQxoP9wEhvkc1swrX6oHQiN9AVdSWdt" psql "$DB_URL" -c "DROP DATABASE IF EXISTS pallcare;"
    
    # Create fresh database
    PGPASSWORD="ubcgvwXWWOliJ3NzA0lHNmnZQZoToF2r0TQxoP9wEhvkc1swrX6oHQiN9AVdSWdt" psql "$DB_URL" -c "CREATE DATABASE pallcare;"
    
    # Restore from backup
    echo "Restoring from backup file..."
    PGPASSWORD="ubcgvwXWWOliJ3NzA0lHNmnZQZoToF2r0TQxoP9wEhvkc1swrX6oHQiN9AVdSWdt" psql "$DB_URL" -d pallcare -f "$BACKUP_FILE"
    
    echo "Database restored from backup successfully!"
    
    # Check and ensure assessment data is correctly set up after restore
    echo "Checking and ensuring assessment data..."
    python scripts/check_assessments_data.py
  else
    echo "Backup file not found. Using default initialization and seeding..."
    # Initialize the database
    echo "Initializing database tables..."
    python run.py create_db
    
    # Initialize protocols before seeding
    echo "Initializing protocols..."
    python scripts/protocol_ingest.py
    
    # Seed the database with test data
    echo "Seeding database with sample data..."
    python run.py seed_db
  fi
  
  echo "Database initialization and seeding complete!"
  echo "Default login credentials:"
  echo "  Admin: admin / password123"
  echo "  Nurse: nurse1 / password123"
  echo "  Physician: physician / password123"
else
  echo "DEV_STATE is not set to TEST. Skipping database initialization."
fi

# Start the application
echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:5000 --workers 4 run:app