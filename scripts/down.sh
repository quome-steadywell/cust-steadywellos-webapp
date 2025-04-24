#!/bin/bash
# SteadywellOS Shutdown Script

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Stopping Palliative Care Platform    ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if .env file exists and load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"
if [ -f "$ENV_FILE" ]; then
  source .env
else
  echo "❌ Error: .env file not found at $ENV_FILE"
  exit 1
fi

# Backup database before stopping
if [ "${DEV_STATE}" = "TEST" ]; then
  echo -e "${GREEN}Creating database backup before shutdown...${NC}"
  # Create backup directory if it doesn't exist
  mkdir -p ./data/backup

  # Set backup file paths with date encoding
  BACKUP_DIR="./data/backup"
  DATE=$(date +%Y%m%d)
  DATE_BACKUP="$BACKUP_DIR/pallcare_db.$DATE.sql"
  STANDARD_BACKUP="$BACKUP_DIR/pallcare_db.sql"
  LATEST_BACKUP="$BACKUP_DIR/pallcare_db.latest.sql"

  # Create the backup to date-encoded file
  echo -e "${GREEN}Creating backup: $DATE_BACKUP${NC}"
  docker-compose exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > "$DATE_BACKUP"

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Date-encoded backup created successfully!${NC}"

    # Update the standard backup file (without date)
    echo -e "${GREEN}Updating standard backup: $STANDARD_BACKUP${NC}"
    cp -f "$DATE_BACKUP" "$STANDARD_BACKUP"

    # Create the "latest" backup file as an additional fallback
    echo -e "${GREEN}Creating latest backup: $LATEST_BACKUP${NC}"
    cp -f "$DATE_BACKUP" "$LATEST_BACKUP"

    if [ $? -eq 0 ]; then
      echo -e "${GREEN}Backup files updated successfully!${NC}"
    else
      echo -e "${YELLOW}Warning: Failed to update some backup files.${NC}"
    fi
  else
    echo -e "${RED}Warning: Failed to create database backup.${NC}"
  fi
fi

# Stop containers
echo -e "${GREEN}Stopping containers...${NC}"
docker-compose down

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}  SteadywellOS has been stopped!      ${NC}"
echo -e "${GREEN}=======================================${NC}"
echo -e "Use \"just up\" to start the application again"
echo -e "${GREEN}=======================================${NC}"
