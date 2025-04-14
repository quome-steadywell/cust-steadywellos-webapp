#!/bin/bash
# debug_push_to_quome.sh - Debug version to track down deployment issues

# Use set -x to show all commands as they're executed
set -x

# Get source directory and environment file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"

# Load API key
if [ -f "$ENV_FILE" ]; then
    API_KEY=$(grep -E '^(CLOUD_API_KEY|QUOME_KEY|QUOME_API_KEY)=' "$ENV_FILE" | head -1 | cut -d '=' -f2)
    echo "API key found: ${API_KEY:0:5}..."
    
    # Check DEV_STATE for testing mode
    DEV_STATE=$(grep '^DEV_STATE=' "$ENV_FILE" | cut -d '=' -f2)
    if [[ "$DEV_STATE" == "TEST" ]]; then
        CURL_SSL_OPTION="-k"
        echo "Using -k flag for curl"
    fi
else
    echo "No .env file found!"
    exit 1
fi

# Cloud configuration
CLOUD_ORG_ID="86880079-c52c-4e5f-9501-101f8a779c66"
CLOUD_APP_ID="cd32baa7-f14e-4035-9ec3-056f4aba5985"
CLOUD_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID"

# Check current configuration
echo "Checking current configuration..."
CURRENT_CONFIG=$(curl $CURL_SSL_OPTION -L -s -m 30 -X GET \
    -H "Authorization: Bearer $API_KEY" \
    "$CLOUD_API_URL")

echo "Current configuration response length: ${#CURRENT_CONFIG}"
echo "First 300 characters of current configuration:"
echo "$CURRENT_CONFIG" | head -c 300

# Define a simple test payload that just updates the app name without changing port
TEST_PAYLOAD=$(cat <<EOF
{
    "name": "palliative-care-test",
    "spec": {
        "port": 5000,
        "containers": [
            {
                "image": "technophobe01/palliative-carer-platform:intel-0.0.3",
                "name": "app",
                "port": 5000,
                "tmp_dirs": [
                    "/var/tmp/"
                ],
                "registry_secret": "pallcare-docker-credentials"
            }
        ]
    }
}
EOF
)

echo "Test payload:"
echo "$TEST_PAYLOAD"

# Try the PUT request with timeout
echo "Attempting PUT request..."
TEST_RESPONSE=$(curl $CURL_SSL_OPTION -L -s -m 30 -w "\nStatus Code: %{http_code}\n" -X PUT \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "$TEST_PAYLOAD" \
    "$CLOUD_API_URL")

echo "PUT response:"
echo "$TEST_RESPONSE"

# Check HTTP status code
HTTP_STATUS=$(echo "$TEST_RESPONSE" | grep "Status Code:" | awk '{print $3}')
echo "HTTP status code: $HTTP_STATUS"

if [[ "$HTTP_STATUS" -ge 200 && "$HTTP_STATUS" -lt 300 ]]; then
    echo "SUCCESS! Request succeeded with HTTP $HTTP_STATUS"
else
    echo "ERROR! Request failed with HTTP $HTTP_STATUS"
fi

# Wait a moment
echo "Waiting 5 seconds to let changes propagate..."
sleep 5

# Verify by getting app again
VERIFY_CONFIG=$(curl $CURL_SSL_OPTION -L -s -m 30 -X GET \
    -H "Authorization: Bearer $API_KEY" \
    "$CLOUD_API_URL")

echo "Verification response length: ${#VERIFY_CONFIG}"
echo "First 300 characters of verification response:"
echo "$VERIFY_CONFIG" | head -c 300
