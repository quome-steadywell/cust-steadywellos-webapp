#!/bin/bash
# Database Initialization Script

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Database Initialization             ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if containers are running
if ! docker-compose ps | grep -q "web\|db"; then
  echo -e "${RED}Containers are not running. Please start them first with 'just up'.${NC}"
  exit 1
fi

# Initialize the database
echo -e "${GREEN}Initializing database tables...${NC}"
docker-compose exec web python run.py create_db

# Initialize protocols
echo -e "${GREEN}Initializing protocols in the database...${NC}"
docker-compose exec web python scripts/protocol_ingest.py

echo -e "${GREEN}Database initialization complete!${NC}"