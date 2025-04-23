#!/bin/bash

# Get script directory and environment file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"

# Check if .env file exists
if [ -f "$ENV_FILE" ]; then
    # Get API key - try all possible env var names
    API_KEY=$(grep -E '^(CLOUD_API_KEY|QUOME_KEY|QUOME_API_KEY)=' "$ENV_FILE" | head -1 | cut -d '=' -f2)
    
    if [ -n "$API_KEY" ]; then
        echo "Bearer Token: $API_KEY"
    else
        echo "❌ No API key found in .env file"
        exit 1
    fi
else
    echo "❌ .env file not found at $ENV_FILE"
    exit 1
fi
