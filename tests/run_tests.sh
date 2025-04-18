#!/bin/bash

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  SteadwellOS Test Suite              ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Install test dependencies
echo -e "${GREEN}Installing test dependencies...${NC}"
pip install -r tests/requirements.txt

# Run service layer tests
echo -e "${GREEN}Running service layer tests...${NC}"
python -m pytest tests/test_anthropic_client.py tests/test_rag_service.py tests/test_twilio_service.py -v

# Run UI tests
echo -e "${GREEN}Running UI tests...${NC}"
python -m pytest tests/ui -v

# Run date handling tests if specified
if [ "$1" == "--all" ] || [ "$1" == "--dates" ]; then
  echo -e "${GREEN}Running date handling tests...${NC}"
  python -m pytest tests/test_date_handling.py -v
fi

echo -e "${GREEN}All tests completed.${NC}"
