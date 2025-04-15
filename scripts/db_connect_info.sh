#!/bin/bash

# Get script directory and environment file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"

# Cloud configuration
CLOUD_ORG_ID="86880079-c52c-4e5f-9501-101f8a779c66"
SECRETS_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/secrets"

# Load API key from .env
if [ -f "$ENV_FILE" ]; then
    API_KEY=$(grep -E '^(CLOUD_API_KEY|QUOME_KEY|QUOME_API_KEY)=' "$ENV_FILE" | head -1 | cut -d '=' -f2)
    
    # Check if in test mode
    DEV_STATE=$(grep '^DEV_STATE=' "$ENV_FILE" | cut -d '=' -f2)
    if [[ "$DEV_STATE" == "TEST" ]]; then
        CURL_SSL_OPTION="-k"
        echo "Using -k flag for curl (SSL verification disabled)"
    fi
    
    if [ -n "$API_KEY" ]; then
        echo "API key found: ${API_KEY:0:5}..."
    else
        echo "❌ No API key found in .env file"
        exit 1
    fi
else
    echo "❌ .env file not found at $ENV_FILE"
    exit 1
fi

# List all secrets
echo "Retrieving list of secrets..."
SECRETS_RESPONSE=$(curl $CURL_SSL_OPTION -s -X GET \
    -H "Authorization: Bearer $API_KEY" \
    "$SECRETS_API_URL")

# Check if the response is valid JSON
if ! echo "$SECRETS_RESPONSE" | jq . >/dev/null 2>&1; then
    echo "❌ Invalid response (not valid JSON):"
    echo "$SECRETS_RESPONSE"
    exit 1
fi

# Display secrets information
echo "$SECRETS_RESPONSE" | jq .

# Check for specific secrets
echo "Checking for specific secrets..."
echo "$SECRETS_RESPONSE" | jq '.secrets[] | {name: .name, type: .type, created: .create_at}'

echo ""
echo "Note: For security reasons, secret values are not included in the API response."
