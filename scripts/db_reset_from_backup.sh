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

echo -e "${GREEN}Restoring from backup...${NC}"
BACKUP_FILE="./data/backup/pallcare_db.sql"
if [ -f "$BACKUP_FILE" ]; then
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
echo -e "${GREEN}Checking and fixing assessment data...${NC}"
docker-compose exec web python scripts/fix_assessments.py

echo -e "${GREEN}Database reset complete!${NC}"
echo -e "${GREEN}Default login credentials:${NC}"
echo -e "  Admin: ${YELLOW}admin / password123${NC}"
echo -e "  Nurse: ${YELLOW}nurse1 / password123${NC}"
echo -e "  Physician: ${YELLOW}physician / password123${NC}"
echo
echo -e "${RED}IMPORTANT: Change the default passwords in production!${NC}"