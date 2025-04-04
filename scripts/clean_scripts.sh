#!/bin/bash
# Script to clean up and ensure script naming consistency

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Script Cleanup and Organization      ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Rename files to follow consistent naming conventions
if [ -f "scripts/fix_assessments.py" ]; then
  echo -e "${GREEN}Renaming fix_assessments.py to check_assessments_data.py...${NC}"
  cp scripts/fix_assessments.py scripts/check_assessments_data.py
  rm scripts/fix_assessments.py
fi

if [ -f "scripts/check_assessments.py" ] && [ ! -f "scripts/check_assessments_api.py" ]; then
  echo -e "${GREEN}Renaming check_assessments.py to check_assessments_api.py...${NC}"
  mv scripts/check_assessments.py scripts/check_assessments_api.py
fi

# Ensure correct permissions
echo -e "${GREEN}Setting execution permissions on shell scripts...${NC}"
chmod +x scripts/*.sh

echo -e "${GREEN}Script cleanup completed successfully!${NC}"