#!/bin/bash
# Database Reset Script using the backup

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Database Reset from Backup         ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if containers are running
if ! docker-compose ps | grep -q "web\|db"; then
  echo -e "${RED}Containers are not running. Please start them first with 'just up'.${NC}"
  exit 1
fi

# Confirm with user
if [ "$1" != "--force" ]; then
  echo -e "${RED}WARNING: This will reset the database using the latest backup file.${NC}"
  read -p "Are you sure you want to continue? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Database reset cancelled.${NC}"
    exit 0
  fi
else
  echo -e "${YELLOW}Forcing database reset without confirmation...${NC}"
fi

# Load environment variables
source .env

# Reset the database
echo -e "${GREEN}Dropping existing database...${NC}"
docker-compose exec db psql -U $POSTGRES_USER -c "DROP DATABASE IF EXISTS $POSTGRES_DB;" postgres
docker-compose exec db psql -U $POSTGRES_USER -c "CREATE DATABASE $POSTGRES_DB;" postgres

echo -e "${GREEN}Finding latest backup file...${NC}"
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
  echo -e "${GREEN}Restoring from backup: $(basename $BACKUP_FILE)...${NC}"
  # Copy the backup file to the container
  docker-compose exec -T db bash -c "cat > /tmp/backup.sql" < $BACKUP_FILE
  
  # Restore from the backup file
  docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /tmp/backup.sql
  
  # Clean up the temporary file
  docker-compose exec db rm /tmp/backup.sql
  
  echo -e "${GREEN}Database restored from backup successfully!${NC}"
else
  echo -e "${RED}Backup file not found at $BACKUP_FILE${NC}"
  echo -e "${YELLOW}Using default database seeding instead...${NC}"
  
  echo -e "${GREEN}Initializing database tables...${NC}"
  docker-compose exec web python run.py create_db
  
  echo -e "${GREEN}Seeding database with sample data...${NC}"
  docker-compose exec web python run.py seed_db
  
  # Clean up any duplicate protocols
  echo -e "${GREEN}Cleaning up database protocols...${NC}"
  docker-compose exec web python scripts/clean_db.py
fi

# Ensure assessments data is properly populated
echo -e "${GREEN}Checking and ensuring assessment data...${NC}"
docker-compose exec web python scripts/check_assessments_data.py

echo -e "${GREEN}Database reset complete!${NC}"
echo -e "${GREEN}Default login credentials:${NC}"
echo -e "  Admin: ${YELLOW}admin / password123${NC}"
echo -e "  Nurse: ${YELLOW}nurse1 / password123${NC}"
echo -e "  Physician: ${YELLOW}physician / password123${NC}"
echo
echo -e "${RED}IMPORTANT: Change the default passwords in production!${NC}"