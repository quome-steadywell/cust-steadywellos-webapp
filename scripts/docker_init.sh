#!/bin/bash
# SteadywellOS Docker Initialization Script
# This script sets up and initializes SteadywellOS in Docker containers

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===============================================${NC}"
echo -e "${YELLOW}  SteadywellOS Docker Initialization Script    ${NC}"
echo -e "${YELLOW}===============================================${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker and Docker Compose.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose.${NC}"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${GREEN}Creating .env file from template...${NC}"
    cp .env.example .env
    
    # Update database URL for Docker
    sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:postgres@db:5432/palliative_care_db|g' .env
    
    # Set Postgres environment variables
    echo "POSTGRES_USER=postgres" >> .env
    echo "POSTGRES_PASSWORD=postgres" >> .env
    echo "POSTGRES_DB=palliative_care_db" >> .env
    
    echo -e "${YELLOW}Please update the .env file with your API keys and other configurations.${NC}"
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

# Build and start the Docker containers
echo -e "${GREEN}Building and starting Docker containers...${NC}"
docker-compose up -d --build

# Wait for the database to be ready
echo -e "${GREEN}Waiting for the database to be ready...${NC}"
sleep 10

# Initialize the database
echo -e "${GREEN}Initializing the database...${NC}"
docker-compose exec web flask create_db

# Ask if user wants to seed the database
read -p "Do you want to seed the database with initial data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Seeding the database...${NC}"
    docker-compose exec web flask seed_db
    echo -e "${GREEN}Database seeded successfully!${NC}"
fi

echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}  SteadywellOS Docker Initialization Complete     ${NC}"
echo -e "${GREEN}=================================================${NC}"
echo
echo -e "The application is now running at: ${YELLOW}http://localhost:5000${NC}"
echo
echo -e "Default admin credentials:"
echo -e "  Username: ${YELLOW}admin${NC}"
echo -e "  Password: ${YELLOW}password123${NC}"
echo
echo -e "${RED}IMPORTANT: Change the default password in production!${NC}"
echo
echo -e "Docker commands:"
echo -e "  View logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "  Stop containers: ${YELLOW}docker-compose stop${NC}"
echo -e "  Start containers: ${YELLOW}docker-compose start${NC}"
echo -e "  Destroy containers: ${YELLOW}docker-compose down${NC}"
echo -e "  Destroy containers and volumes: ${YELLOW}docker-compose down -v${NC}"