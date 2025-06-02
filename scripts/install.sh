#!/bin/bash
# SteadywellOS Installation Script

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
chmod +x scripts/*.sh
chmod +x scripts/*.py

# Checking prerequisites
echo -e "${GREEN}Checking prerequisites...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker to continue.${NC}"
    echo -e "Visit https://docs.docker.com/get-docker/ for installation instructions."
    echo
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose to continue.${NC}"
    echo -e "Visit https://docs.docker.com/compose/install/ for installation instructions."
    echo
    exit 1
fi

# Check if Just is installed
if ! command -v just &> /dev/null; then
    echo -e "${YELLOW}Just command runner is not installed. It's recommended for easier command execution.${NC}"
    echo -e "Visit https://github.com/casey/just#installation for installation instructions."
    echo
    read -p "Do you want to continue without Just? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Installation aborted.${NC}"
        exit 1
    fi
fi

# Check if 1Password cli is installed
if ! command -v op &> /dev/null; then
    echo -e "${YELLOW}1Password CLI is not installed. It's recommended to avoid storing secrets on disk.${NC}"
    echo -e "Visit https://developer.1password.com/docs/cli/get-started/ for more information."
    echo
    read -p "Do you want to continue without 1Password CLI? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Installation aborted.${NC}"
        exit 1
    fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env.secrets"

# Check for .env file
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}ERROR: .env.secrets file not found at $ENV_FILE${NC}"
    echo -e "${YELLOW}Please create a .env.secrets file based on the provided example${NC}"
    echo
    echo -e "   cp .env.example .env.secrets${NC}"
    echo
    echo -e "${YELLOW}and add all required values or 1Password secret references${NC}"
    echo
    exit 1
fi

echo
echo -e "${GREEN}Installation completed! You can now start the application:${NC}"
echo -e "${YELLOW}  just up${NC}    - If you have Just installed"
echo -e "${YELLOW}  ./scripts/up.sh${NC} - If you don't have Just installed"
echo
