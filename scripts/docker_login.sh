#!/bin/bash
# docker_login.sh - Login to Docker Hub using credentials from .env file

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Error: .env file not found at $ENV_FILE"
  exit 1
fi

# Extract username and password/token from .env file
USERNAME=$(grep '^DOCKER_USERNAME=' "$ENV_FILE" | cut -d '=' -f2)
PASSWORD=$(grep '^DOCKER_PASSWORD=' "$ENV_FILE" | cut -d '=' -f2)
TOKEN=$(grep '^DOCKER_TOKEN=' "$ENV_FILE" | cut -d '=' -f2)

# Check if credentials are available
if [ -z "$USERNAME" ]; then
    echo "❌ DOCKER_USERNAME not found in .env file"
    exit 1
fi

# Try login with token first, then with password
if [ -n "$TOKEN" ]; then
    echo "🔑 Logging in with token..."
    echo "$TOKEN" | docker login -u "$USERNAME" --password-stdin
elif [ -n "$PASSWORD" ]; then
    echo "🔑 Logging in with password..."
    echo "$PASSWORD" | docker login -u "$USERNAME" --password-stdin
else
    echo "❌ Neither DOCKER_TOKEN nor DOCKER_PASSWORD found in .env file"
    exit 1
fi

# Check login status
if [ $? -eq 0 ]; then
    echo "✅ Successfully logged in to Docker Hub as $USERNAME"
    exit 0
else
    echo "❌ Failed to login to Docker Hub"
    exit 1
fi
