#!/bin/bash
# Run date handling tests in Docker environment

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Date Handling Tests (Docker)        ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if containers are running
if ! docker-compose ps | grep -q "web\|db"; then
  echo -e "${RED}Containers are not running. Please start them first with 'docker-compose up -d'.${NC}"
  exit 1
fi

# Run date seeding in Docker container
echo -e "${GREEN}Seeding test data for date handling tests...${NC}"
docker-compose exec web python -c "from src.utils.db_seeder import seed_date_check_data; seed_date_check_data()"

# Run the date handling tests in Docker container
echo -e "${GREEN}Running date handling tests...${NC}"
docker-compose exec web python -m pytest tests/test_date_handling.py -v

echo -e "${GREEN}Date handling tests completed!${NC}"