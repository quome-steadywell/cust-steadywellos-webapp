#!/bin/bash
# Database Seeding Script

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Database Seeding                   ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if containers are running
if ! docker-compose ps | grep -q "web\|db"; then
  echo -e "${RED}Containers are not running. Please start them first with 'just up'.${NC}"
  exit 1
fi

# Seed the database
echo -e "${GREEN}Seeding database with sample data...${NC}"
docker-compose exec web python run.py seed_db

echo -e "${GREEN}Database seeding complete!${NC}"
echo -e "${GREEN}Default login credentials:${NC}"
echo -e "  Admin: ${YELLOW}admin / password123${NC}"
echo -e "  Nurse: ${YELLOW}nurse1 / password123${NC}"
echo -e "  Physician: ${YELLOW}physician / password123${NC}"
echo
echo -e "${RED}IMPORTANT: Change the default passwords in production!${NC}"