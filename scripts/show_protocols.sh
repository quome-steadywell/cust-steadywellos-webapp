#!/bin/bash
# Show existing protocols in the database

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
  source .env
fi

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Protocol Information               ${NC}"
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

# If DEV_STATE is TEST and protocols aren't found, initialize them
docker-compose exec -T web python scripts/check_protocols.py > /tmp/protocol_check_output
PROTOCOL_COUNT=$(grep -c "Protocol found" /tmp/protocol_check_output || echo "0")

if [ "${DEV_STATE}" = "TEST" ] && [ "$PROTOCOL_COUNT" = "0" ]; then
  echo -e "${YELLOW}No protocols found and DEV_STATE is TEST. Initializing protocols...${NC}"
  docker-compose exec -T web python scripts/protocol_ingest.py
  echo -e "${GREEN}Protocols initialized.${NC}"

  # Check protocols again
  echo -e "${GREEN}Checking protocols in the database...${NC}"
  docker-compose exec web python scripts/check_protocols.py
else
  # Display the output we already captured
  cat /tmp/protocol_check_output
fi

echo -e "${GREEN}Protocol check complete!${NC}"
