#!/bin/bash
# Upgrade Anthropic Library

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Upgrading Anthropic Library          ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if containers are running
if ! docker-compose ps | grep -q "web\\|db"; then
  echo -e "${RED}Containers are not running. Please start them first with 'just up'.${NC}"
  exit 1
fi

# Upgrade anthropic library in the container
echo -e "${GREEN}Upgrading anthropic library to v0.18.1...${NC}"
docker-compose exec -T web pip install --upgrade anthropic==0.18.1

echo -e "${GREEN}Anthropic library upgraded successfully!${NC}"