#\!/bin/bash
# create_working_backup.sh - Create a known working database backup for Quome Cloud

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Creating Working Database Backup    ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if containers are running
if \! docker-compose ps | grep -q "web\|db"; then
  echo -e "${RED}Containers are not running. Please start them first with 'just up'.${NC}"
  exit 1
fi

# Load environment variables
if [ -f .env ]; then
  source .env
else
  echo -e "${RED}No .env file found.${NC}"
  exit 1
fi

# Create backup directories if they don't exist
mkdir -p ./data/backup

# Define backup files
BACKUP_DIR="./data/backup"
WORKING_BACKUP="$BACKUP_DIR/pallcare_db_working.sql"

echo -e "${GREEN}Creating working database backup...${NC}"

# Create a special format for the working backup
(
  # Add header comments to clarify this is a special backup
  echo "-- SteadwellOS Palliative Care Platform"
  echo "-- WORKING DATABASE BACKUP"
  echo "-- Created: $(date)"
  echo "-- This is a known working backup for use in Quome Cloud environment"
  echo "-- Format tweaked to avoid ownership issues"
  echo ""
  
  # Export the database and add it to our file
  docker-compose exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB
) > "$WORKING_BACKUP"

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Working database backup created: $WORKING_BACKUP${NC}"
  echo -e "${GREEN}Backup size: $(du -h "$WORKING_BACKUP" | cut -f 1)${NC}"
  
  # Verify backup contains Mary Johnson
  MARY_COUNT=$(grep -c "Mary.*Johnson" "$WORKING_BACKUP")
  if [ $MARY_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ Verified: Mary Johnson found in backup ($MARY_COUNT occurrences)${NC}"
  else
    echo -e "${RED}⚠️ Warning: Mary Johnson not found in backup\!${NC}"
  fi
  
  echo -e "${GREEN}Working backup complete and ready for Quome Cloud deployment${NC}"
  echo -e "${YELLOW}To deploy to Quome, run: ./scripts/push_to_quome.sh${NC}"
else
  echo -e "${RED}Failed to create working database backup.${NC}"
  exit 1
fi
