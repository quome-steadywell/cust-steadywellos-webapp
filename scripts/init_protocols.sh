#!/bin/bash
# Initialize protocols in the database

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Protocol Initialization             ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if .env file exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Error: .env file not found at $ENV_FILE"
  exit 1
fi

# Check if containers are running
if ! docker-compose ps | grep -q "web\\|db"; then
  echo -e "${RED}Containers are not running. Please start them first with 'just up'.${NC}"
  exit 1
fi

# Execute protocol ingest script
echo -e "${GREEN}Initializing protocols in the database...${NC}"
docker-compose exec web python scripts/protocol_ingest.py $@

echo -e "${GREEN}Protocol initialization complete!${NC}"
