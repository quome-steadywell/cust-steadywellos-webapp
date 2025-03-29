#!/bin/bash
# SteadywellOS Installation Script
# This script guides the user through the installation process

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}       SteadywellOS Installer            ${NC}"
echo -e "${BLUE}  Palliative Care Coordination Platform  ${NC}"
echo -e "${BLUE}==========================================${NC}"
echo 

# Set permissions
echo -e "${GREEN}Setting script permissions...${NC}"
chmod +x setup_permissions.sh
./setup_permissions.sh

# Choose installation method
echo -e "${YELLOW}Please choose an installation method:${NC}"
echo "1) Local installation (Python virtual environment)"
echo "2) Docker installation (Containerized environment)"
echo "3) Exit"
echo

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo -e "${GREEN}Starting local installation...${NC}"
        ./init.sh
        ;;
    2)
        echo -e "${GREEN}Starting Docker installation...${NC}"
        ./scripts/docker_init.sh
        ;;
    3)
        echo -e "${YELLOW}Installation canceled.${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}Installation completed!${NC}"
echo -e "${YELLOW}For more information, refer to the documentation in the docs/ directory.${NC}"
echo