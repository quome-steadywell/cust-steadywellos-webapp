#!/bin/bash
# test_push_to_quome.sh - Test script to create Docker credentials secret in Quome Cloud

set -e  # Exit on error

# Get script directory and environment file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"

# Cloud deployment configuration - update these with your values
CLOUD_ORG_ID="86880079-c52c-4e5f-9501-101f8a779c66"
SECRET_NAME="pallcare-docker-credentials"  # Name for your Docker credentials secret
SECRETS_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/secrets"

# Alternative URL in case the API has changed
ALT_SECRETS_API_URL="https://quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/secrets"

echo "🔧 Using primary API URL: $SECRETS_API_URL"
echo "🔧 Alternative API URL (if needed): $ALT_SECRETS_API_URL"

# Allow user to choose the API URL
read -p "Use alternative API URL instead? (y/n): " USE_ALT_URL
if [[ "$USE_ALT_URL" == "y" ]]; then
    SECRETS_API_URL=$ALT_SECRETS_API_URL
    echo "Switched to alternative API URL: $SECRETS_API_URL"
fi

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE"
    exit 1
fi

echo "🔍 Reading credentials from .env file..."

# Load Docker credentials from .env
USERNAME=$(grep '^DOCKER_USERNAME=' "$ENV_FILE" | cut -d '=' -f2)
if [ -z "$USERNAME" ]; then
    echo "❌ Error: DOCKER_USERNAME not found in .env file"
    exit 1
fi
echo "✅ Found Docker username: $USERNAME"

DOCKER_TOKEN=$(grep '^DOCKER_TOKEN=' "$ENV_FILE" | cut -d '=' -f2)
if [ -z "$DOCKER_TOKEN" ]; then
    echo "❌ Error: DOCKER_TOKEN not found in .env file"
    exit 1
fi
echo "✅ Found Docker token (first 5 chars): ${DOCKER_TOKEN:0:5}..."

# Load API key from .env
API_KEY=$(grep -E '^(CLOUD_API_KEY|QUOME_KEY|QUOME_API_KEY)=' "$ENV_FILE" | head -1 | cut -d '=' -f2)
if [ -z "$API_KEY" ]; then
    echo "❌ Error: API_KEY not found in .env file"
    exit 1
fi
echo "✅ Found API key (first 5 chars): ${API_KEY:0:5}..."

# Create Docker credentials secret payload
echo "📦 Preparing Docker credentials secret payload..."
DOCKER_SECRET_PAYLOAD=$(cat <<EOF
{
    "name": "$SECRET_NAME",
    "type": "docker-credentials",
    "description": "Docker Hub credentials for $USERNAME",
    "secret": {
        "auths": {
            "https://index.docker.io/v1/": {
                "username": "$USERNAME",
                "password": "$DOCKER_TOKEN"
            }
        }
    }
}
EOF
)

# Show payload for verification (masking password)
MASKED_PAYLOAD=$(echo "$DOCKER_SECRET_PAYLOAD" | sed "s/\"password\": \"[^\"]*\"/\"password\": \"********\"/g")
echo "Payload:"
echo "$MASKED_PAYLOAD"

# Confirmation before proceeding
read -p "Proceed with secret creation? (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" ]]; then
    echo "Operation cancelled."
    exit 0
fi

# First, check existing secrets with verbose logging
echo "🔍 Checking existing secrets..."
echo "API URL: $SECRETS_API_URL"

GET_DEBUG_FILE="/tmp/quome_get_secrets_debug_$(date +%s).log"
echo "GET debug log will be saved to: $GET_DEBUG_FILE"

EXISTING_SECRETS=$(curl -k -L -s -v -w "\nStatus Code: %{http_code}\nResponse Time: %{time_total}s\n" \
    -H "Authorization: Bearer $API_KEY" \
    "$SECRETS_API_URL" 2>"$GET_DEBUG_FILE")

# Extract HTTP status code from GET request
GET_HTTP_STATUS=$(echo "$EXISTING_SECRETS" | grep "Status Code:" | awk '{print $3}')

# Extract request ID if present in GET response
GET_REQUEST_ID=$(echo "$EXISTING_SECRETS" | grep -o '"requestId":"[^"]*"' | cut -d'"' -f4)
if [ -z "$GET_REQUEST_ID" ]; then
    GET_REQUEST_ID=$(echo "$EXISTING_SECRETS" | grep -o '"request_id":"[^"]*"' | cut -d'"' -f4)
fi
if [ -z "$GET_REQUEST_ID" ]; then
    GET_REQUEST_ID=$(echo "$EXISTING_SECRETS" | grep -o '"request-id":"[^"]*"' | cut -d'"' -f4)
fi

# Extract return code if present in GET response
GET_RETURN_CODE=$(echo "$EXISTING_SECRETS" | grep -o '"returnCode":"[^"]*"' | cut -d'"' -f4)
if [ -z "$GET_RETURN_CODE" ]; then
    GET_RETURN_CODE=$(echo "$EXISTING_SECRETS" | grep -o '"return_code":"[^"]*"' | cut -d'"' -f4)
fi
if [ -z "$GET_RETURN_CODE" ]; then
    GET_RETURN_CODE=$(echo "$EXISTING_SECRETS" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
fi

# Check for header request ID in debug log
GET_DEBUG_REQUEST_ID=""
if [ -f "$GET_DEBUG_FILE" ]; then
    GET_DEBUG_REQUEST_ID=$(grep -i "x-request-id:" "$GET_DEBUG_FILE" | head -1 | awk '{print $2}' | tr -d '\r')
fi

echo "----- GET EXISTING SECRETS RESPONSE -----"
echo "HTTP status code: $GET_HTTP_STATUS"
if [ -n "$GET_REQUEST_ID" ]; then
    echo "Request ID: $GET_REQUEST_ID"
elif [ -n "$GET_DEBUG_REQUEST_ID" ]; then
    echo "Request ID from headers: $GET_DEBUG_REQUEST_ID"
else 
    echo "Request ID: Not found in response"
fi
if [ -n "$GET_RETURN_CODE" ]; then
    echo "Return code: $GET_RETURN_CODE"
else
    echo "Return code: Not found in response"
fi
echo "Response body:"
echo "$EXISTING_SECRETS" | grep -v "Status Code:" | grep -v "Response Time:"
echo "-----------------------------------------"

# Check if the existing secrets request was successful
if [[ "$GET_HTTP_STATUS" -ge 200 && "$GET_HTTP_STATUS" -lt 300 ]]; then
    if [[ "$EXISTING_SECRETS" == *"\"secrets\":null"* || "$EXISTING_SECRETS" == *"\"secrets\": null"* ]]; then
        echo "✓ GET request successful, but no secrets found in this organization."
    elif [[ "$EXISTING_SECRETS" == *"\"secrets\":"* ]]; then
        echo "✓ GET request successful, found existing secrets in organization."
        # Try to count how many secrets exist
        SECRET_COUNT=$(echo "$EXISTING_SECRETS" | grep -o '"name":' | wc -l)
        if [[ "$SECRET_COUNT" -gt 0 ]]; then
            echo "  Found approximately $SECRET_COUNT secret(s)"
        fi
    else
        echo "⚠ GET request response format unexpected. See full response above."
    fi
else
    echo "⚠ GET request failed with HTTP status $GET_HTTP_STATUS"
    # Extract errors from debug log
    if [ -f "$GET_DEBUG_FILE" ]; then
        CONNECTION_ERRORS=$(grep -i "error\|failed" "$GET_DEBUG_FILE" | grep -v "grep")
        if [ -n "$CONNECTION_ERRORS" ]; then
            echo "Connection errors from debug log:"
            echo "$CONNECTION_ERRORS"
        fi
    fi
fi

# Ask if user wants to proceed with secret creation
echo "📡 Ready to send request to create new Docker credentials secret..."
echo "API URL: $SECRETS_API_URL"

# Save detailed debugging output to a file
DEBUG_FILE="/tmp/quome_secret_debug_$(date +%s).log"
echo "Debug log will be saved to: $DEBUG_FILE"

# Execute the API request with verbose output saved to debug file
RESPONSE=$(curl -k -L -s -v -w "\nStatus Code: %{http_code}\nResponse Time: %{time_total}s\n" \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "$DOCKER_SECRET_PAYLOAD" \
    "$SECRETS_API_URL" 2>"$DEBUG_FILE")

# Extract HTTP status code
HTTP_STATUS=$(echo "$RESPONSE" | grep "Status Code:" | awk '{print $3}')

# Extract request ID if present in response
REQUEST_ID=$(echo "$RESPONSE" | grep -o '"requestId":"[^"]*"' | cut -d'"' -f4)
if [ -z "$REQUEST_ID" ]; then
    REQUEST_ID=$(echo "$RESPONSE" | grep -o '"request_id":"[^"]*"' | cut -d'"' -f4)
fi
if [ -z "$REQUEST_ID" ]; then
    REQUEST_ID=$(echo "$RESPONSE" | grep -o '"request-id":"[^"]*"' | cut -d'"' -f4)
fi

# Extract return code if present in response
RETURN_CODE=$(echo "$RESPONSE" | grep -o '"returnCode":"[^"]*"' | cut -d'"' -f4)
if [ -z "$RETURN_CODE" ]; then
    RETURN_CODE=$(echo "$RESPONSE" | grep -o '"return_code":"[^"]*"' | cut -d'"' -f4)
fi
if [ -z "$RETURN_CODE" ]; then
    RETURN_CODE=$(echo "$RESPONSE" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
fi

# Display response info with additional details
echo "----- RESPONSE INFO -----"
echo "HTTP status code: $HTTP_STATUS"
if [ -n "$REQUEST_ID" ]; then
    echo "Request ID: $REQUEST_ID"
else
    echo "Request ID: Not found in response"
fi
if [ -n "$RETURN_CODE" ]; then
    echo "Return code: $RETURN_CODE"
else
    echo "Return code: Not found in response"
fi
echo "Response body preview:"
echo "$RESPONSE" | grep -v "Status Code:" | grep -v "Response Time:"
echo "-------------------------"

# Inspect debug log for additional information
echo "Analyzing debug log for additional information..."
if [ -f "$DEBUG_FILE" ]; then
    # Extract any request ID from headers
    DEBUG_REQUEST_ID=$(grep -i "x-request-id:" "$DEBUG_FILE" | head -1 | awk '{print $2}' | tr -d '\r')
    if [ -n "$DEBUG_REQUEST_ID" ]; then
        echo "Request ID from headers: $DEBUG_REQUEST_ID"
    fi
    
    # Check for specific error messages
    ERROR_MESSAGES=$(grep -i "error" "$DEBUG_FILE" | grep -v "grep")
    if [ -n "$ERROR_MESSAGES" ]; then
        echo "Error messages from debug log:"
        echo "$ERROR_MESSAGES"
    fi
    
    # Check connection details
    CONNECTION_INFO=$(grep -i "connected to" "$DEBUG_FILE")
    if [ -n "$CONNECTION_INFO" ]; then
        echo "Connection details:"
        echo "$CONNECTION_INFO"
    fi
fi

# Check response status with enhanced debugging
if [[ "$HTTP_STATUS" -ge 200 && "$HTTP_STATUS" -lt 300 ]]; then
    echo "✅ SUCCESS: Docker credentials secret '$SECRET_NAME' created successfully!"
    echo "This secret can now be referenced in your app deployment."
elif [[ "$HTTP_STATUS" -eq 409 || "$RESPONSE" == *"already exists"* ]]; then
    echo "ℹ️ INFO: Secret '$SECRET_NAME' already exists."
    echo "You can use this existing secret in your app deployment."
else
    echo "❌ ERROR: Failed to create Docker credentials secret (HTTP status: $HTTP_STATUS)"
    
    # Enhanced error analysis
    echo ""
    echo "📊 Error Analysis:"
    
    if [[ "$HTTP_STATUS" -eq 0 ]]; then
        echo "- No HTTP response received. This could indicate connectivity issues."
        echo "- Check if the API endpoint is accessible from your network."
        echo "- Try the alternative API URL by running the script again and selecting 'y'."
    elif [[ "$HTTP_STATUS" -eq 401 || "$HTTP_STATUS" -eq 403 ]]; then
        echo "- Authentication failure (HTTP $HTTP_STATUS)"
        echo "- Your API key may be invalid or expired."
        echo "- Check that you have permission to create secrets in this organization."
    elif [[ "$HTTP_STATUS" -eq 404 ]]; then
        echo "- Resource not found (HTTP $HTTP_STATUS)"
        echo "- The API endpoint may have changed."
        echo "- Verify your organization ID is correct: $CLOUD_ORG_ID"
        echo "- Try the alternative API URL by running the script again and selecting 'y'."
    elif [[ "$HTTP_STATUS" -eq 400 ]]; then
        echo "- Bad request (HTTP $HTTP_STATUS)"
        echo "- The API payload format may be incorrect."
        echo "- The API schema may have changed."
    fi
    
    echo ""
    echo "Response details:"
    echo "$RESPONSE" | grep -v "Status Code:" | grep -v "Response Time:"
    
    echo ""
    echo "Curl debug log: $DEBUG_FILE"
    echo "Try checking the Quome Cloud documentation for the latest API format."
    
    # Offer to try alternative URL
    if [[ "$SECRETS_API_URL" != "$ALT_SECRETS_API_URL" ]]; then
        echo ""
        read -p "Try with alternative API URL ($ALT_SECRETS_API_URL)? (y/n): " TRY_ALT
        if [[ "$TRY_ALT" == "y" ]]; then
            echo "Retrying with alternative URL..."
            SECRETS_API_URL=$ALT_SECRETS_API_URL
            
            # Execute the API request again with the alternate URL
            RESPONSE=$(curl -k -L -s -w "\nStatus Code: %{http_code}\nResponse Time: %{time_total}s\n" \
                -X POST \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $API_KEY" \
                -d "$DOCKER_SECRET_PAYLOAD" \
                "$SECRETS_API_URL" 2>>"$DEBUG_FILE")
            
            HTTP_STATUS=$(echo "$RESPONSE" | grep "Status Code:" | awk '{print $3}')
            
            echo "----- RETRY RESPONSE INFO -----"
            echo "HTTP status code: $HTTP_STATUS"
            echo "Response body preview:"
            echo "$RESPONSE" | grep -v "Status Code:" | grep -v "Response Time:"
            echo "--------------------------------"
            
            if [[ "$HTTP_STATUS" -ge 200 && "$HTTP_STATUS" -lt 300 ]]; then
                echo "✅ SUCCESS with alternative URL: Docker credentials secret created successfully!"
                echo "This secret can now be referenced in your app deployment."
                # Continue with success path
            else
                echo "❌ ERROR: Failed with alternative URL as well."
                exit 1
            fi
        else
            exit 1
        fi
    else
        exit 1
    fi
fi

echo ""
echo "📋 Summary:"
echo "- Organization ID: $CLOUD_ORG_ID"
echo "- Secret Name: $SECRET_NAME"
echo "- Docker Username: $USERNAME"
echo "- API URL: $SECRETS_API_URL"
echo ""
echo "🔍 GET Request:"
echo "- HTTP Status: $GET_HTTP_STATUS"
if [ -n "$GET_REQUEST_ID" ]; then
    echo "- Request ID: $GET_REQUEST_ID"
elif [ -n "$GET_DEBUG_REQUEST_ID" ]; then
    echo "- Request ID: $GET_DEBUG_REQUEST_ID (from headers)"
fi
if [ -n "$GET_RETURN_CODE" ]; then
    echo "- Return Code: $GET_RETURN_CODE"
fi
echo "- Debug Log: $GET_DEBUG_FILE"
echo ""
echo "🔹 POST Request:"
echo "- HTTP Status: $HTTP_STATUS"
if [ -n "$REQUEST_ID" ]; then
    echo "- Request ID: $REQUEST_ID"
elif [ -n "$DEBUG_REQUEST_ID" ]; then
    echo "- Request ID: $DEBUG_REQUEST_ID (from headers)"
fi
if [ -n "$RETURN_CODE" ]; then
    echo "- Return Code: $RETURN_CODE"
fi
echo "- Debug Log: $DEBUG_FILE"
echo ""
if [ "$DEPLOYMENT_SUCCESS" = "true" ]; then
    echo "✅ RESULT: Success"
    echo ""
    echo "To use this secret in your app deployment, add this to your container spec:"
    echo '"registry_secret": "'$SECRET_NAME'"'
    echo ""
    echo "Example usage in push_to_quome.sh payload:"
    echo '{
    "name": "your-app-name",
    "spec": {
        "containers": [
            {
                "image": "your-image-name",
                "name": "app",
                "port": 8080,
                "registry_secret": "'$SECRET_NAME'",
                ...
            }
        ]
    }
}'
else
    echo "❌ RESULT: Failed"
    echo ""
    echo "Please check the debug logs for more information:"
    echo "- GET request: $GET_DEBUG_FILE"
    echo "- POST request: $DEBUG_FILE"
fi
