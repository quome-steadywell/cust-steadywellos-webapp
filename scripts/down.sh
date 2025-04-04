#!/bin/bash
# SteadywellOS Shutdown Script

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Stopping Palliative Care Platform    ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Backup database before stopping
if [ -f .env ]; then
  source .env
  if [ "${DEV_STATE}" = "TEST" ]; then
    echo -e "${GREEN}Creating database backup before shutdown...${NC}"
    # Create backup directory if it doesn't exist
    mkdir -p ./data/backup
    
    # Set backup file paths
    BACKUP_DIR="./data/backup"
    STANDARD_BACKUP="$BACKUP_DIR/pallcare_db.sql"
    
    # Create the backup
    docker-compose exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > "$STANDARD_BACKUP"
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}Database backup created successfully!${NC}"
    else
      echo -e "${YELLOW}Warning: Failed to create database backup.${NC}"
    fi
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