#!/bin/bash
# Database Reset Script

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Database Reset                     ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if containers are running
if ! docker-compose ps | grep -q "web\|db"; then
  echo -e "${RED}Containers are not running. Please start them first with 'just up'.${NC}"
  exit 1
fi

# Confirm with user
if [ "$1" != "--force" ]; then
  echo -e "${RED}WARNING: This will reset the database and all data will be lost!${NC}"
  read -p "Are you sure you want to continue? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Database reset cancelled.${NC}"
    exit 0
  fi
else
  echo -e "${YELLOW}Forcing database reset without confirmation...${NC}"
fi

# Reset the database
echo -e "${GREEN}Dropping existing database...${NC}"
docker-compose exec web python run.py drop_db

echo -e "${GREEN}Initializing database tables...${NC}"
docker-compose exec web python run.py create_db

# Skip protocol ingest that relies on Anthropic API
# We'll use protocols from the seed_database function instead
echo -e "${GREEN}Skipping external protocol creation due to API limitations...${NC}"
echo -e "${GREEN}Using default protocols from the seeder...${NC}"

echo -e "${GREEN}Seeding database with sample data...${NC}"
docker-compose exec web python run.py seed_db

echo -e "${GREEN}Database reset complete!${NC}"
echo -e "${GREEN}Default login credentials:${NC}"
echo -e "  Admin: ${YELLOW}admin / password123${NC}"
echo -e "  Nurse: ${YELLOW}nurse1 / password123${NC}"
echo -e "  Physician: ${YELLOW}physician / password123${NC}"
echo
echo -e "${RED}IMPORTANT: Change the default passwords in production!${NC}"