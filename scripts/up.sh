#!/bin/bash
# SteadywellOS Startup Script

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Starting Palliative Care Platform   ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Load environment variables
if [ -f .env ]; then
  source .env
fi

# Check if Docker is running
echo -e "${GREEN}Checking if Docker is running...${NC}"
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}Docker is not running or not installed. Please start Docker and try again.${NC}"
  exit 1
fi
echo -e "${GREEN}Docker is running!${NC}"

# Build and start the containers
echo -e "${GREEN}Building and starting containers...${NC}"
docker-compose up -d --build
echo -e "${GREEN}Containers started! Services are initializing...${NC}"

# Wait for the database to be ready
echo -e "${GREEN}Waiting for database to be ready...${NC}"
sleep 10

# Ensure Anthropic library is updated
echo -e "${GREEN}Checking Anthropic library version...${NC}"
ANTHROPIC_VERSION=$(docker-compose exec -T web pip show anthropic | grep Version | awk '{print $2}')
REQUIRED_VERSION="0.18.1"

if [[ "$ANTHROPIC_VERSION" != "$REQUIRED_VERSION" ]]; then
  echo -e "${YELLOW}Upgrading Anthropic library from $ANTHROPIC_VERSION to $REQUIRED_VERSION...${NC}"
  docker-compose exec -T web pip install --upgrade anthropic==$REQUIRED_VERSION
  echo -e "${GREEN}Anthropic library upgraded successfully!${NC}"
else
  echo -e "${GREEN}Anthropic library is already at version $ANTHROPIC_VERSION${NC}"
fi

# Initialize and seed database if in TEST mode
if [ "${DEV_STATE}" = "TEST" ]; then
  echo -e "${YELLOW}DEV_STATE is set to TEST. Restoring database from backup...${NC}"
  
  # Find the latest backup file by date encoding
  BACKUP_DIR="./data/backup"
  
  # First, check for date-encoded backups (pallcare_db.YYYYMMDD.sql)
  LATEST_DATE_BACKUP=$(ls -t $BACKUP_DIR/pallcare_db.20*.sql 2>/dev/null | head -1)
  
  # If no date-encoded backup is found, fall back to non-dated backup
  if [ -n "$LATEST_DATE_BACKUP" ]; then
    BACKUP_FILE="$LATEST_DATE_BACKUP"
    DATE_PART=$(basename $BACKUP_FILE | sed 's/pallcare_db\.\([0-9]*\)\.sql/\1/')
    echo -e "${GREEN}Found date-encoded backup from $DATE_PART: $(basename $BACKUP_FILE)${NC}"
  else
    # Try fallback options in order of preference
    if [ -f "$BACKUP_DIR/pallcare_db.latest.sql" ]; then
      BACKUP_FILE="$BACKUP_DIR/pallcare_db.latest.sql"
      echo -e "${YELLOW}No date-encoded backup found. Using latest backup: $(basename $BACKUP_FILE)${NC}"
    elif [ -f "$BACKUP_DIR/pallcare_db.sql" ]; then
      BACKUP_FILE="$BACKUP_DIR/pallcare_db.sql"
      echo -e "${YELLOW}No date-encoded or latest backup found. Using standard backup: $(basename $BACKUP_FILE)${NC}"
    elif [ -f "$BACKUP_DIR/pallcare_db_working.sql" ]; then
      BACKUP_FILE="$BACKUP_DIR/pallcare_db_working.sql"
      echo -e "${YELLOW}No other backups found. Using working backup: $(basename $BACKUP_FILE)${NC}"
    else
      BACKUP_FILE=""
    fi
  fi
  
  if [ -n "$BACKUP_FILE" ]; then
    echo -e "${GREEN}Setting up database from backup: $(basename $BACKUP_FILE)...${NC}"
    
    # Create a fresh database
    echo -e "${GREEN}Dropping existing database...${NC}"
    docker-compose exec -T db psql -U $POSTGRES_USER -c "DROP DATABASE IF EXISTS $POSTGRES_DB;" postgres
    docker-compose exec -T db psql -U $POSTGRES_USER -c "CREATE DATABASE $POSTGRES_DB;" postgres
    
    # Restore from backup
    echo -e "${GREEN}Restoring from backup file...${NC}"
    docker-compose exec -T db bash -c "cat > /tmp/backup.sql" < $BACKUP_FILE
    docker-compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /tmp/backup.sql
    docker-compose exec -T db rm /tmp/backup.sql
    
    echo -e "${GREEN}Database restored from backup successfully!${NC}"
    
    # Check and ensure assessment data is correctly set up after restore
    echo -e "${GREEN}Checking and ensuring assessment data...${NC}"
    docker-compose exec -T web python scripts/check_assessments_data.py
    
    # Fix Mary Johnson's data specifically to prevent common issues
    echo -e "${GREEN}Fixing Mary Johnson's patient record...${NC}"
    docker-compose exec -T web python scripts/fix_mary_johnson.py
  else
    echo -e "${YELLOW}Backup file not found. Using default initialization and seeding...${NC}"
    # Initialize the database
    echo -e "${GREEN}Initializing database tables...${NC}"
    docker-compose exec -T web python run.py create_db
    
    # Initialize protocols before seeding
    echo -e "${GREEN}Initializing protocols...${NC}"
    docker-compose exec -T web python scripts/protocol_ingest.py
    
    # Seed the database with test data
    echo -e "${GREEN}Seeding database with sample data...${NC}"
    docker-compose exec -T web python run.py seed_db
  fi
  
  echo -e "${GREEN}Database initialization and seeding complete!${NC}"
  echo -e "${GREEN}Default login credentials:${NC}"
  echo -e "  Admin: ${YELLOW}admin / password123${NC}"
  echo -e "  Nurse: ${YELLOW}nurse1 / password123${NC}"
  echo -e "  Physician: ${YELLOW}physician / password123${NC}"
else
  echo -e "${YELLOW}DEV_STATE is not set to TEST. Skipping database initialization.${NC}"
fi

# Final message
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}  SteadywellOS is now running!        ${NC}"
echo -e "${GREEN}=======================================${NC}"
echo -e "The Palliative Care Platform is available at:"
echo -e "  ${YELLOW}http://localhost:8080${NC}"
echo
echo -e "Use \"just logs\" to view application logs"
echo -e "Use \"just down\" to stop the application"
echo -e "${GREEN}=======================================${NC}"