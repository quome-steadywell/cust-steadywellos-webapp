#!/bin/bash
# Database Backup Script

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Database Backup                    ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if containers are running
if ! docker-compose ps | grep -q "web\|db"; then
  echo -e "${RED}Containers are not running. Please start them first with 'just up'.${NC}"
  exit 1
fi

# Load environment variables
source .env

# Create backup directories if they don't exist
mkdir -p ./data/backup

# Get current date for backup file
DATE=$(date +%Y%m%d)
BACKUP_DIR="./data/backup"
BACKUP_FILE="$BACKUP_DIR/pallcare_db.$DATE.sql"
STANDARD_BACKUP="$BACKUP_DIR/pallcare_db.sql"

echo -e "${GREEN}Creating database backup...${NC}"
docker-compose exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Database backup created: $BACKUP_FILE${NC}"
  
  # Update the standard backup file
  echo -e "${GREEN}Updating standard backup file: $STANDARD_BACKUP${NC}"
  cp -f "$BACKUP_FILE" "$STANDARD_BACKUP"
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Standard backup file updated successfully!${NC}"
  else
    echo -e "${RED}Failed to update standard backup file.${NC}"
    exit 1
  fi
else
  echo -e "${RED}Failed to create database backup.${NC}"
  exit 1
fi

echo -e "${GREEN}Database backup process completed successfully!${NC}"