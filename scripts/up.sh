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