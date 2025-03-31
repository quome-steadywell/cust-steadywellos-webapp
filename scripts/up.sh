#!/bin/bash
# SteadywellOS Startup Script

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Starting Palliative Care Platform   ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Load environment variables
if [ -f .env ]; then
  source .env
fi

# Check if Docker is running
echo -e "${GREEN}Checking if Docker is running...${NC}"
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}Docker is not running or not installed. Please start Docker and try again.${NC}"
  exit 1
fi
echo -e "${GREEN}Docker is running!${NC}"

# Build and start the containers
echo -e "${GREEN}Building and starting containers...${NC}"
docker-compose up -d --build
echo -e "${GREEN}Containers started! Services are initializing...${NC}"

# Wait for the database to be ready
echo -e "${GREEN}Waiting for database to be ready...${NC}"
sleep 10

# Ensure Anthropic library is updated
echo -e "${GREEN}Checking Anthropic library version...${NC}"
ANTHROPIC_VERSION=$(docker-compose exec -T web pip show anthropic | grep Version | awk '{print $2}')
REQUIRED_VERSION="0.18.1"

if [[ "$ANTHROPIC_VERSION" != "$REQUIRED_VERSION" ]]; then
  echo -e "${YELLOW}Upgrading Anthropic library from $ANTHROPIC_VERSION to $REQUIRED_VERSION...${NC}"
  docker-compose exec -T web pip install --upgrade anthropic==$REQUIRED_VERSION
  echo -e "${GREEN}Anthropic library upgraded successfully!${NC}"
else
  echo -e "${GREEN}Anthropic library is already at version $ANTHROPIC_VERSION${NC}"
fi

# Initialize and seed database if in TEST mode
if [ "${DEV_STATE}" = "TEST" ]; then
  echo -e "${YELLOW}DEV_STATE is set to TEST. Initializing and seeding database...${NC}"
  # Initialize the database
  echo -e "${GREEN}Initializing database tables...${NC}"
  docker-compose exec -T web python run.py create_db
  
  # Seed the database with test data
  echo -e "${GREEN}Seeding database with sample data...${NC}"
  docker-compose exec -T web python run.py seed_db
  
  # Initialize protocols directly
  echo -e "${GREEN}Initializing protocols...${NC}"
  docker-compose exec -T web python scripts/protocol_ingest.py
  
  echo -e "${GREEN}Database initialization and seeding complete!${NC}"
  echo -e "${GREEN}Default login credentials:${NC}"
  echo -e "  Admin: ${YELLOW}admin / password123${NC}"
  echo -e "  Nurse: ${YELLOW}nurse1 / password123${NC}"
  echo -e "  Physician: ${YELLOW}physician / password123${NC}"
else
  echo -e "${YELLOW}DEV_STATE is not set to TEST. Skipping database initialization.${NC}"
fi

# Final message
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}  SteadywellOS is now running!        ${NC}"
echo -e "${GREEN}=======================================${NC}"
echo -e "The Palliative Care Platform is available at:"
echo -e "  ${YELLOW}http://localhost:8080${NC}"
echo
echo -e "Use \"just logs\" to view application logs"
echo -e "Use \"just down\" to stop the application"
echo -e "${GREEN}=======================================${NC}"