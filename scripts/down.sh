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

# Stop containers
echo -e "${GREEN}Stopping containers...${NC}"
docker-compose down

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}  SteadywellOS has been stopped!      ${NC}"
echo -e "${GREEN}=======================================${NC}"
echo -e "Use \"just up\" to start the application again"
echo -e "${GREEN}=======================================${NC}"