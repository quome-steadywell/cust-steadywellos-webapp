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
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose to continue.${NC}"
    echo -e "Visit https://docs.docker.com/compose/install/ for installation instructions."
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

# Create or update environment variables file
echo -e "${GREEN}Setting up environment variables...${NC}"
cat > .env << EOF
# Database Configuration
POSTGRES_USER=pallcare
POSTGRES_PASSWORD=pallcarepass
POSTGRES_DB=pallcare_db
DATABASE_URL=postgresql://pallcare:pallcarepass@db:5432/pallcare_db

# Security Keys
SECRET_KEY=dev-secret-key-replace-in-production
JWT_SECRET_KEY=dev-jwt-secret-key-replace-in-production

# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development

# API Keys (replace with real keys in production)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
ANTHROPIC_API_KEY=your_anthropic_api_key
EOF
echo -e "${GREEN}Environment variables configured.${NC}"

echo
echo -e "${GREEN}Installation completed! You can now start the application:${NC}"
echo -e "${YELLOW}  just up${NC}    - If you have Just installed"
echo -e "${YELLOW}  ./scripts/up.sh${NC} - If you don't have Just installed"
echo