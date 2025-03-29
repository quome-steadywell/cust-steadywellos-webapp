#!/bin/bash
# SteadywellOS Initialization Script
# This script sets up the Docker environment and initializes the database for the Palliative Care Platform

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Palliative Care Platform Setup      ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if Docker is running
echo -e "${GREEN}Checking if Docker is running...${NC}"
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}Docker is not running or not installed. Please start Docker and try again.${NC}"
  exit 1
fi
echo -e "${GREEN}Docker is running!${NC}"

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

# Update docker-compose configuration
echo -e "${GREEN}Checking Docker Compose configuration...${NC}"
if grep -q '"5000:5000"' docker-compose.yml; then
  echo -e "${GREEN}Updating port in docker-compose.yml to avoid conflicts...${NC}"
  sed -i '' 's/"5000:5000"/"8080:5000"/' docker-compose.yml
fi

# Remove version from docker-compose.yml as it's obsolete
if grep -q "^version:" docker-compose.yml; then
  echo -e "${GREEN}Removing obsolete version tag from docker-compose.yml...${NC}"
  sed -i '' 's/^version:.*$/# Docker Compose Configuration/' docker-compose.yml
fi
echo -e "${GREEN}Docker Compose configuration updated.${NC}"

# Stop and remove any existing containers and volumes
echo -e "${GREEN}Cleaning up existing containers and volumes...${NC}"
docker-compose down -v 2>/dev/null || true
echo -e "${GREEN}Cleanup completed.${NC}"

# Build and start the containers
echo -e "${GREEN}Building and starting containers...${NC}"
docker-compose up -d --build
echo -e "${GREEN}Containers started! Waiting for services to initialize...${NC}"

# Wait for the database to be ready
echo -e "${GREEN}Waiting for database to be ready...${NC}"
sleep 10

# Initialize the database and seed data
echo -e "${GREEN}Initializing database tables...${NC}"
docker exec palliative_care_platform-web-1 python run.py create_db
echo -e "${GREEN}Seeding database with sample data...${NC}"
docker exec palliative_care_platform-web-1 python run.py seed_db

# Final message
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}  Initialization Complete!             ${NC}"
echo -e "${GREEN}=======================================${NC}"
echo -e "The Palliative Care Platform is now running at:"
echo -e "  ${YELLOW}http://localhost:8080${NC}"
echo
echo -e "Default login credentials:"
echo -e "  Admin: ${YELLOW}admin / password123${NC}"
echo -e "  Nurse: ${YELLOW}nurse1 / password123${NC}"
echo -e "  Physician: ${YELLOW}physician / password123${NC}"
echo
echo -e "${RED}IMPORTANT: Change the default passwords in production!${NC}"
echo -e "${GREEN}=======================================${NC}"