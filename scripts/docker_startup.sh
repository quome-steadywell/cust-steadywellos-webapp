#!/bin/bash
# docker_startup.sh - Production version of the startup script for Quome Cloud

# /app is always read-only
# /tmp and /tmp/pallcare are writable
# These paths are setup via push_to_quome

# Write startup header directly to stdout/stderr for Quome logging
echo "=== QUOME CLOUD STARTUP LOG $(date) ==="
echo "Container starting with hostname: $(hostname)"
echo "Environment: DEV_STATE=${DEV_STATE:-unset}"

# Exit on any error
set -e

echo "Starting Palliative Care Platform..."

# Set up /tmp directory for writable files
echo "Setting up temporary directory for writable files..."
TMP_DIR="/tmp/pallcare"

# Create logs directory in /tmp to avoid permission issues
mkdir -p /tmp/logs
# Create symlink from /app/logs to /tmp/logs for backward compatibility
if [ ! -L "/app/logs" ] && [ ! -d "/app/logs" ]; then
  ln -s /tmp/logs /app/logs 2>/dev/null || true
fi

# Wait for database to be ready
echo "Waiting for database to be available..."

# Check if we're running in Quome Cloud
if [ -n "$PALLCARE_URL" ] || [ -n "$QUOME_CLOUD" ]; then
  echo "Using Quome Cloud database connection..."
  
  DB_URL=$PALLCARE_URL
  # We have the PALLCARE_URL set since we're in quome cloud, so we can extract
  # all the db info from there
  DB_USER=$(echo "$DB_URL" | sed -E 's/.*\/\/([^:]*).*/\1/')
  DB_PASS=$(echo "$DB_URL" | sed -E 's/.*:(.*)@.*/\1/')
  DB_HOST=$(echo "$DB_URL" | sed -E 's/.*@([^:\/]*)[:\/].*/\1/')
  DB_PORT=$(echo "$DB_URL" | sed -E 's/.*:([^@\/]*)\/.*/\1/')
  DB_PORT="${DB_PORT:-5432}"
  DB_NAME=$(echo "$DB_URL" | sed -E 's/.*\/([^?]*).*/\1/')
  
  # Debug output for database connection
  echo "Quome environment detected" >/dev/stdout
  echo "DB Host: $DB_HOST" >/dev/stdout
  echo "DB Port: $DB_PORT" >/dev/stdout
  echo "DB User: $DB_USER" >/dev/stdout
  
  # This is likely a Quome Cloud deployment
  IS_QUOME_CLOUD=true
else
  echo "Using standard database connection..."
  DB_HOST="${POSTGRES_HOST:-db}"
  DB_PORT="${POSTGRES_PORT:-5432}"
  DB_USER="${POSTGRES_USER:-postgres}"
  IS_QUOME_CLOUD=false
fi

# Try to connect to Postgres for up to 60 seconds (12 tries, 5 seconds each)
RETRIES=12
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER || [ $RETRIES -eq 0 ]; do
  echo "Waiting for postgres server to be ready, $((RETRIES--)) remaining attempts..."
  sleep 5
done

# Initialize and seed database if in TEST mode
if [ "${DEV_STATE}" = "TEST" ]; then
  echo "DEV_STATE is set to TEST. Setting up test database..."
  
  # Prioritize these specific backup files first, then fall back to date ordering
  BACKUP_DIR="/app/data/backup"
  
  # Check for the known good backup files, in order of preference
  for PREFERRED_BACKUP in "$BACKUP_DIR/pallcare_db_working.sql" "$BACKUP_DIR/pallcare_db.20250415.sql" "$BACKUP_DIR/pallcare_db.sql"; do
    if [ -f "$PREFERRED_BACKUP" ]; then
      LATEST_BACKUP="$PREFERRED_BACKUP"
      echo "Found preferred backup file: $(basename $PREFERRED_BACKUP)"
      break
    fi
  done
  
  # If no preferred backup found, fall back to latest by date
  if [ -z "$LATEST_BACKUP" ]; then
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/pallcare_db*.sql 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
      echo "Using latest dated backup file: $(basename $LATEST_BACKUP)"
    fi
  fi
  
  BACKUP_FILE="/tmp/pallcare_db.sql"
  
  if [ -n "$LATEST_BACKUP" ]; then
    echo "Copying backup file to tmp directory..."
    cp "$LATEST_BACKUP" "$BACKUP_FILE"
    echo "Setting up database from backup..."
    
    # Use the direct connection URL for Quome deployment
    echo "Setting up database using Quome Cloud connection..."
    
    # In Quome environment, we should recreate the database from scratch
    if [ "$IS_QUOME_CLOUD" = true ]; then
      echo "Setting up database in Quome environment..." >/dev/stdout
    
      # Use constructed URL for Quome Cloud
      DB_USER=$(echo "$DB_URL" | sed -E 's/.*\/\/([^:]*).*/\1/')
      DB_PASS=$(echo "$DB_URL" | sed -E 's/.*:(.*)@.*/\1/')
      DB_HOST=$(echo "$DB_URL" | sed -E 's/.*@([^:\/]*)[:\/].*/\1/')
      DB_NAME=$(echo "$DB_URL" | sed -E 's/.*\/([^?]*).*/\1/')
      
      # Connect to postgres database to perform operations
      POSTGRES_DB="postgres"
      
      # First try to drop and then recreate the database
      echo "Attempting to drop database '$DB_NAME' if it exists..." >/dev/stdout
      DROP_RESULT=0
      DROP_OUTPUT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -p $DB_PORT -d "$POSTGRES_DB" -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>&1) || DROP_RESULT=$?
      
      if [ "$DROP_RESULT" -eq 0 ]; then
        echo "Database dropped successfully or didn't exist." >/dev/stdout
      else
        echo "Error dropping database: $DROP_OUTPUT" >/dev/stdout
        echo "Will try to continue anyway..." >/dev/stdout
      fi
      
      # Now create a fresh database
      echo "Creating a fresh database '$DB_NAME'..." >/dev/stdout
      CREATE_RESULT=0
      CREATE_OUTPUT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -p $DB_PORT -d "$POSTGRES_DB" -c "CREATE DATABASE $DB_NAME;" 2>&1) || CREATE_RESULT=$?
      
      if [ "$CREATE_RESULT" -eq 0 ]; then
        echo "Database created successfully." >/dev/stdout
      else
        echo "Error creating database: $CREATE_OUTPUT" >/dev/stdout
        
        # Try again with template0 as a fallback
        echo "Trying again with template0..." >/dev/stdout
        PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -p $DB_PORT -d "$POSTGRES_DB" -c "CREATE DATABASE $DB_NAME TEMPLATE template0;" 2>/dev/stdout || {
          echo "All database creation attempts failed. Will try to continue anyway..." >/dev/stdout
        }
      fi
    fi
    
    # Build the connection URL
    # Use the PALLCARE_URL environment variable if available, fall back to constructed URL
    if [ -n "$PALLCARE_URL" ]; then
      # Make sure there are no trailing spaces in the URL
      DB_URL=$(echo "$PALLCARE_URL" | tr -d ' ')
    else
      DB_URL="postgresql://cust-86880079-c52c-4e5f-9501-101f8a779c66.pallcare:ubcgvwXWWOliJ3NzA0lHNmnZQZoToF2r0TQxoP9wEhvkc1swrX6oHQiN9AVdSWdt@pallcare-cluster.databases:5432/pallcare"
    fi
    
    echo "Testing database connection..." >/dev/stdout
    if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -p $DB_PORT -c "SELECT 1;" "$DB_NAME" 2>/dev/stdout; then
      echo "✅ Database connection successful" >/dev/stdout
    else
      echo "⚠️ Database connection failed, will retry after creating tables" >/dev/stdout
    fi
    
    echo "Using database connection: ${DB_URL}"
    
    # The database name should already be in the connection string
    # We need to first create tables and then restore data
    
    # Extract database name from connection URL for clarity
    DB_NAME=$(echo "$DB_URL" | sed -E 's/.*\/([^?]*).*/\1/')
    echo "Using database: $DB_NAME"
    
    # Direct restoration approach - prepare a modified backup without ownership issues
    export DATABASE_URL="$DB_URL"
    export TEMP_DIR="$TMP_DIR"
    export PYTHONUNBUFFERED=1
    export FLASK_APP="run.py"
    
    # Create a temporary modified backup with ownership adjusted to our user
    echo "Preparing modified backup file..." >/dev/stdout
    MODIFIED_BACKUP="/tmp/modified_backup.sql"
    
    # These are the main issues we need to fix:
    # 1. Role "pallcare" does not exist - replace with our user
    # 2. Table already exists errors - add DROP TABLE IF EXISTS
    # 3. Type already exists errors - add DROP TYPE IF EXISTS
    
    # Start with a preamble that ensures clean slate
    echo "-- Modified backup with ownership fixes" > "$MODIFIED_BACKUP"
    echo "SET client_min_messages TO warning;" >> "$MODIFIED_BACKUP"
    echo "-- Drop objects in correct order to avoid dependency conflicts" >> "$MODIFIED_BACKUP"
    echo "DROP TABLE IF EXISTS assessments CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TABLE IF EXISTS calls CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TABLE IF EXISTS medications CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TABLE IF EXISTS patients CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TABLE IF EXISTS protocols CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TABLE IF EXISTS audit_logs CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TABLE IF EXISTS users CASCADE;" >> "$MODIFIED_BACKUP"
    
    echo "-- Drop enum types" >> "$MODIFIED_BACKUP"
    echo "DROP TYPE IF EXISTS callstatus CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TYPE IF EXISTS followuppriority CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TYPE IF EXISTS gender CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TYPE IF EXISTS medicationfrequency CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TYPE IF EXISTS medicationroute CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TYPE IF EXISTS protocoltype CASCADE;" >> "$MODIFIED_BACKUP"
    echo "DROP TYPE IF EXISTS userrole CASCADE;" >> "$MODIFIED_BACKUP"
    
    # Regular expressions to replace "OWNER TO pallcare" with our current user
    # and to handle other ownership issues
    cat "$BACKUP_FILE" | \
      sed "s/OWNER TO pallcare/OWNER TO \"$DB_USER\"/g" | \
      sed "s/ALTER TYPE .* OWNER TO pallcare;/-- Ownership line removed/g" | \
      sed "s/ALTER TABLE .* OWNER TO pallcare;/-- Ownership line removed/g" | \
      sed "s/ALTER SEQUENCE .* OWNER TO pallcare;/-- Ownership line removed/g" | \
      sed "s/^CREATE INDEX/CREATE INDEX IF NOT EXISTS/g" | \
      sed "s/^ALTER TABLE .* ADD CONSTRAINT/ALTER TABLE IF EXISTS/g" \
      >> "$MODIFIED_BACKUP"
      
    echo "Modified backup created at $MODIFIED_BACKUP" >/dev/stdout
    
    # Try to restore directly from our modified backup
    echo "Attempting to restore from modified backup file..." >/dev/stdout
    
    # Create schema first
    echo "Creating schema..." >/dev/stdout
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -p $DB_PORT -d "$DB_NAME" -c "CREATE SCHEMA IF NOT EXISTS public; GRANT ALL ON SCHEMA public TO \"$DB_USER\";"
    
    # Now try the restore
    RESTORE_SUCCEEDED=false
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -p $DB_PORT -d "$DB_NAME" -f "$MODIFIED_BACKUP" && RESTORE_SUCCEEDED=true
    
    # If the restore succeeded, we're done
    if [ "$RESTORE_SUCCEEDED" = true ]; then
        echo "Database restored from backup successfully!" >/dev/stdout
        
        # Grant proper permissions to all objects 
        echo "Granting all permissions to current user..." >/dev/stdout
        PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -p $DB_PORT -d "$DB_NAME" -c "
            -- Grant schema 
            GRANT ALL ON SCHEMA public TO \"$DB_USER\";
            
            -- Grant tables
            DO \$\$
            DECLARE
                tabname text;
            BEGIN
                FOR tabname IN 
                    SELECT tablename FROM pg_tables WHERE schemaname = 'public'
                LOOP
                    EXECUTE 'GRANT ALL ON ' || quote_ident(tabname) || ' TO \"$DB_USER\"';  
                END LOOP;
            END \$\$;
            
            -- Grant sequences
            DO \$\$
            DECLARE
                seqname text;
            BEGIN
                FOR seqname IN 
                    SELECT relname FROM pg_class WHERE relkind = 'S' AND relnamespace = 'public'::regnamespace
                LOOP
                    EXECUTE 'GRANT ALL ON SEQUENCE ' || quote_ident(seqname) || ' TO \"$DB_USER\"';
                END LOOP;
            END \$\$;
        "
        
    else
        echo "Backup restore failed, initializing from scratch..." >/dev/stdout
        
        # Create empty tables
        echo "Creating database tables..." >/dev/stdout
        echo "Executing: python run.py create_db" >&2
        python run.py create_db
        echo "Database tables creation completed" >&2
        
        # Initialize protocols first
        echo "Initializing protocols..." >/dev/stdout
        python scripts/protocol_ingest.py
        
        # Seed the database
        echo "Seeding database with sample data..." >/dev/stdout
        python run.py seed_db
        
        echo "Database initialized from scratch successfully!" >/dev/stdout
    fi
    
    # Verify the database has tables (we no longer need to create them as fallback)
    echo "Verifying database tables exist..."
    TABLE_CHECK=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -p $DB_PORT -d "$DB_NAME" -c "\dt" | grep -c "patients")
    if [ "$TABLE_CHECK" -eq 0 ]; then
        echo "❌ Warning: Tables not found after initialization/restore. Attempting to create tables..." >&2
        
        # Create empty tables
        echo "Creating database tables..." >&2
        export TEMP_DIR="$TMP_DIR"
        export PYTHONUNBUFFERED=1
        export FLASK_APP="run.py"
        python run.py create_db
        
        # Check again
        TABLE_CHECK=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -p $DB_PORT -d "$DB_NAME" -c "\dt" | grep -c "patients")
        if [ "$TABLE_CHECK" -eq 0 ]; then
            echo "❌ Error: Tables still not found after create_db. Cannot continue!" >&2
            exit 1
        else
            echo "✅ Database tables created successfully"
        fi
    else
        echo "✅ Database tables verified"
    fi
    
    # Second check: Make sure Mary Johnson exists (common issue)
    echo "Checking for Mary Johnson record..."
    MARY_CHECK=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -p $DB_PORT -d "$DB_NAME" -c "SELECT COUNT(*) FROM patients WHERE first_name='Mary' AND last_name='Johnson'" | grep -c "1")
    
    if [ "$MARY_CHECK" -eq 0 ]; then
        echo "Mary Johnson not found. Running seed again to create essential data..." >/dev/stdout
        # The seed process will create Mary Johnson
        python run.py seed_db
        
        # Now run the assessment data check to create her assessments
        echo "Creating assessment data..." >/dev/stdout
        export TEMP_DIR="$TMP_DIR"
        export PYTHONUNBUFFERED=1
        python scripts/check_assessments_data.py
    else
        echo "Mary Johnson record exists ✅" >/dev/stdout
    fi
    
    # Always fix Mary Johnson's data specifically to prevent common issues
    echo "Ensuring Mary Johnson's patient record is properly configured..."
    python scripts/fix_mary_johnson.py
  else
    echo "Backup file not found. Using default initialization and seeding..."
    
    # Set database URL and temporary directory for Python scripts
    if [ -n "$PALLCARE_URL" ]; then
      echo "Using Quome Cloud database connection for initialization..."
      # Clean up URL by removing any spaces
      CLEANED_URL=$(echo "$PALLCARE_URL" | tr -d ' ')
      export DATABASE_URL="$CLEANED_URL"
      echo "Database URL set to: $DATABASE_URL"
    else
      export DATABASE_URL="postgresql://cust-86880079-c52c-4e5f-9501-101f8a779c66.pallcare:ubcgvwXWWOliJ3NzA0lHNmnZQZoToF2r0TQxoP9wEhvkc1swrX6oHQiN9AVdSWdt@pallcare-cluster.databases:5432/pallcare"
      echo "Using default Database URL: $DATABASE_URL"
    fi
    
    # Set temp directory for application
    export TEMP_DIR="$TMP_DIR"
    export PYTHONUNBUFFERED=1
    
    # Initialize the database
    echo "Initializing database tables..." >&2
    export FLASK_APP="run.py"
    echo "Executing: python run.py create_db (fresh)" >&2
    python run.py create_db
    echo "Database tables creation completed (fresh)" >&2
    
    # Initialize protocols before seeding
    echo "Initializing protocols..."
    python scripts/protocol_ingest.py
    
    # Seed the database with test data
    echo "Seeding database with sample data..." >&2
    echo "Executing: python run.py seed_db" >&2
    python run.py seed_db
    echo "Database seeding completed" >&2
  fi
  
  echo "Database initialization and seeding complete!"
  echo "Default login credentials:"
  echo "  Admin: admin / password123"
  echo "  Nurse: nurse1 / password123"
  echo "  Physician: physician / password123"
else
  echo "DEV_STATE is not set to TEST. Skipping database initialization."
fi

# Set required environment variables for the application
# Set DATABASE_URL if PALLCARE_URL is available
if [ -n "$PALLCARE_URL" ]; then
  echo "Setting DATABASE_URL from PALLCARE_URL for application..."
  # Make sure there are no trailing spaces in the URL
  CLEANED_URL=$(echo "$PALLCARE_URL" | tr -d ' ')
  export DATABASE_URL="$CLEANED_URL"
  echo "Database URL set to: $DATABASE_URL"
else
  # Fallback to hardcoded URL without spaces
  export DATABASE_URL="postgresql://cust-86880079-c52c-4e5f-9501-101f8a779c66.pallcare:ubcgvwXWWOliJ3NzA0lHNmnZQZoToF2r0TQxoP9wEhvkc1swrX6oHQiN9AVdSWdt@pallcare-cluster.databases:5432/pallcare"
  echo "Using default Database URL: $DATABASE_URL"
fi

# Always set temp directory for application
export TEMP_DIR="$TMP_DIR"
export PYTHONUNBUFFERED=1

# Make sure app knows to save files to /tmp
echo "Setting application to use /tmp for all writable files"

# Start the application
echo "Starting Gunicorn server..."
echo "Startup script completed, launching Gunicorn with 4 workers"

# Use exec to replace the current process with gunicorn
# This ensures gunicorn gets signals directly and logs go to Docker logs
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --access-logfile="-" --error-logfile="-" run:app
