#!/bin/bash
# debug_push_to_quome.sh - Debug version to track down deployment issues

# Use set -x to show all commands as they're executed
set -x

# Get source directory and environment file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"

# Load API key and Docker credentials
if [ -f "$ENV_FILE" ]; then
    # Get API key
    API_KEY=$(grep -E '^(CLOUD_API_KEY|QUOME_KEY|QUOME_API_KEY)=' "$ENV_FILE" | head -1 | cut -d '=' -f2)
    echo "API key found: ${API_KEY:0:5}..."
    
    # Get Docker username and token
    USERNAME=$(grep '^DOCKER_USERNAME=' "$ENV_FILE" | cut -d '=' -f2)
    echo "Docker username: $USERNAME"
    
    DOCKER_TOKEN=$(grep '^DOCKER_TOKEN=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$DOCKER_TOKEN" ]; then
        echo "Docker token found: ${DOCKER_TOKEN:0:5}..."
    else
        echo "No Docker token found in .env file"
    fi
    
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
DOCKER_SECRET_NAME="pallcare-docker-credentials"

# Create or verify Docker credentials secret
echo "🔑 Ensuring Docker credentials secret exists..."

# Create Docker credentials secret with proper payload structure
DOCKER_SECRET_PAYLOAD=$(cat <<EOF
{
    "name": "$DOCKER_SECRET_NAME",
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

# Check if Docker token is available
if [ -z "$DOCKER_TOKEN" ]; then
    echo "⚠️ Docker token not found in .env file"
    echo "Skipping Docker credentials secret creation."
    echo "The existing secret '$DOCKER_SECRET_NAME' will be used if available."
else
    # Create Docker credentials secret
    echo "📡 Creating Docker credentials secret '$DOCKER_SECRET_NAME'..."
    
    # API URL for secrets
    SECRETS_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/secrets"
    echo "Secrets API URL: $SECRETS_API_URL"
    
    # Save detailed debugging output to a file for inspection if needed
    SECRET_DEBUG_FILE="/tmp/quome_secret_debug_$(date +%s).log"
    
    # Try to create the secret via API (with SSL option if in test mode)
    SECRET_RESPONSE=$(curl $CURL_SSL_OPTION -L -s -w "\nStatus Code: %{http_code}\n" -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "$DOCKER_SECRET_PAYLOAD" \
        "$SECRETS_API_URL" 2>"$SECRET_DEBUG_FILE")
    
    SECRET_STATUS=$(echo "$SECRET_RESPONSE" | grep "Status Code:" | awk '{print $3}')
    
    # Extract request ID if present
    SECRET_REQUEST_ID=$(echo "$SECRET_RESPONSE" | grep -o '"requestId":"[^"]*"' | cut -d'"' -f4)
    if [ -z "$SECRET_REQUEST_ID" ]; then
        SECRET_REQUEST_ID=$(echo "$SECRET_RESPONSE" | grep -o '"request_id":"[^"]*"' | cut -d'"' -f4)
    fi
    
    # Check if the secret was created successfully
    if [[ "$SECRET_STATUS" -ge 200 && "$SECRET_STATUS" -lt 300 ]] || \
       [[ "$SECRET_RESPONSE" == *"\"status\":\"success\""* || "$SECRET_RESPONSE" == *"\"status\":\"ok\""* ]]; then
        echo "✅ Docker credentials secret created or updated successfully"
    elif [[ "$SECRET_STATUS" -eq 409 || "$SECRET_RESPONSE" == *"already exists"* ]]; then
        echo "ℹ️ Secret '$DOCKER_SECRET_NAME' already exists"
    else
        echo "⚠️ Could not create Docker credentials secret (HTTP status: $SECRET_STATUS)"
        if [ -n "$SECRET_REQUEST_ID" ]; then
            echo "Request ID: $SECRET_REQUEST_ID"
        fi
        echo "Response preview:"
        echo "$SECRET_RESPONSE" | head -10
        echo "You may need to create this secret manually via the Quome Cloud dashboard"
        echo "Debug log: $SECRET_DEBUG_FILE"
    fi
fi

# Check current configuration
echo "Checking current configuration..."
CURRENT_CONFIG=$(curl $CURL_SSL_OPTION -L -s -m 30 -X GET \
    -H "Authorization: Bearer $API_KEY" \
    "$CLOUD_API_URL")

echo "Current configuration response length: ${#CURRENT_CONFIG}"
echo "First 300 characters of current configuration:"
echo "$CURRENT_CONFIG" | head -c 300

# Define payload with proper k8s_vars section
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
                    "/tmp",
                    "/tmp/pallcare"
                ],
                "env_vars": {
                    "FLASK_APP": "run.py",
                    "FLASK_ENV": "production"
                },
                "k8s_vars": {
                    "ANTHROPIC_API_KEY": {
                        "name": "anthropic-key",
                        "key": "key"
                    },
                    "DATABASE_URL": {
                        "name": "db-url",
                        "key": "url"
                    },
                    "PALLCARE_URL": {
                        "name": "pallcare-url",
                        "key": "url"
                    }
                },
                "registry_secret": "$DOCKER_SECRET_NAME"
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
    DEPLOYMENT_SUCCESS=true
else
    echo "ERROR! Request failed with HTTP $HTTP_STATUS"
    DEPLOYMENT_SUCCESS=false
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

# Add verification of deployment status if deployment was successful
if [ "$DEPLOYMENT_SUCCESS" = "true" ]; then
    echo "🔍 Verifying deployment status..."
    
    # Wait for a moment to allow deployment to start
    echo "⏳ Waiting 10 seconds for deployment to start..."
    sleep 10
    
    # Check deployment status
    VERIFICATION_ATTEMPTS=0
    MAX_VERIFICATION_ATTEMPTS=6  # Will check for up to 1 minute (6 x 10 seconds)
    DEPLOYMENT_VERIFIED=false
    
    while [ $VERIFICATION_ATTEMPTS -lt $MAX_VERIFICATION_ATTEMPTS ]; do
        VERIFICATION_ATTEMPTS=$((VERIFICATION_ATTEMPTS + 1))
        echo "Verification attempt $VERIFICATION_ATTEMPTS of $MAX_VERIFICATION_ATTEMPTS..."
        
        # Get app status
        APP_STATUS=$(curl $CURL_SSL_OPTION -L -s -X GET \
            -H "Authorization: Bearer $API_KEY" \
            "$CLOUD_API_URL" 2>/dev/null)
        
        # Check for successful deployment indicators
        if [[ "$APP_STATUS" == *"\"status\":\"running\""* || "$APP_STATUS" == *"\"state\":\"running\""* ]]; then
            echo "✅ Deployment verified! Application is running."
            DEPLOYMENT_VERIFIED=true
            break
        elif [[ "$APP_STATUS" == *"\"status\":\"deploying\""* || "$APP_STATUS" == *"\"state\":\"deploying\""* ]]; then
            echo "⏳ Application is still being deployed..."
        elif [[ "$APP_STATUS" == *"\"status\":\"error\""* || "$APP_STATUS" == *"\"state\":\"error\""* ]]; then
            echo "❌ Deployment failed. Application is in error state."
            echo "Error details:"
            echo "$APP_STATUS" | grep -o '"error":"[^"]*"' || echo "No error details available"
            DEPLOYMENT_VERIFIED=false
            break
        else
            echo "🔄 Deployment status is unclear. Current response:"
            echo "$APP_STATUS" | head -10
        fi
        
        # If we haven't verified yet, wait and try again
        if [ "$DEPLOYMENT_VERIFIED" != "true" ] && [ $VERIFICATION_ATTEMPTS -lt $MAX_VERIFICATION_ATTEMPTS ]; then
            echo "⏳ Waiting 10 seconds before next check..."
            sleep 10
        fi
    done
    
    # Final verification message
    if [ "$DEPLOYMENT_VERIFIED" = "true" ]; then
        echo "✅ DEPLOYMENT VERIFICATION SUCCESSFUL!"
        echo "🚀 The application is now running with port configuration:"
        echo "  - App Port: 5000"
        echo "  - Container Port: 5000"
    else
        if [ $VERIFICATION_ATTEMPTS -ge $MAX_VERIFICATION_ATTEMPTS ]; then
            echo "⚠️ Deployment verification timed out after $(($MAX_VERIFICATION_ATTEMPTS * 10)) seconds."
            echo "The deployment might still be in progress."
            echo "Please check the Quome Cloud dashboard manually."
        else
            echo "❌ Deployment verification failed."
            echo "Please check the Quome Cloud dashboard for more details."
        fi
    fi
fi

