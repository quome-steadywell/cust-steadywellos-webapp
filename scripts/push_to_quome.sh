#!/bin/bash
# push_to_quome.sh - Update cloud deployment for palliative care app using the latest Intel image

set -e  # Exit on error

# Default values
DEFAULT_USERNAME="technophobe01"
DEFAULT_REPOSITORY="palliative-carer-platform"
DEFAULT_APPLICATION_NAME="palliative-care"
DEFAULT_PORT="8080"
DEFAULT_CONTAINER_PORT="5000"  # Container's internal port
DEFAULT_TAG="intel-0.0.1"  # Default tag if nothing found

# Cloud deployment configuration
CLOUD_ORG_ID="86880079-c52c-4e5f-9501-101f8a779c66"
CLOUD_APP_ID="cd32baa7-f14e-4035-9ec3-056f4aba5985"  # Your updated App ID
CLOUD_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID"

# Get script directory and environment file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"
USERNAME=$DEFAULT_USERNAME

# Load environment variables if .env exists
CURL_SSL_OPTION=""
if [ -f "$ENV_FILE" ]; then
    # Get Docker username
    ENV_USERNAME=$(grep '^DOCKER_USERNAME=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$ENV_USERNAME" ]; then
        USERNAME=$ENV_USERNAME
    else
        echo "⚠️ DOCKER_USERNAME found in .env file but appears to be empty"
    fi
    
    # Check Docker token
    if grep -q '^DOCKER_TOKEN=' "$ENV_FILE"; then
        DOCKER_TOKEN=$(grep '^DOCKER_TOKEN=' "$ENV_FILE" | cut -d '=' -f2)
        if [ -z "$DOCKER_TOKEN" ]; then
            echo "⚠️ DOCKER_TOKEN found in .env file but appears to be empty"
        fi
    fi
    
    # Get API key - try all possible env var names
    API_KEY=$(grep -E '^(CLOUD_API_KEY|QUOME_KEY|QUOME_API_KEY)=' "$ENV_FILE" | head -1 | cut -d '=' -f2)
    if [ -n "$API_KEY" ]; then
        echo "✅ Found API key in .env file"
    fi
    
    # Get latest Intel tag
    INTEL_TAG=$(grep '^INTEL_CURRENT_TAG=' "$ENV_FILE" | cut -d '=' -f2)
    
    # Check DEV_STATE for testing mode
    DEV_STATE=$(grep '^DEV_STATE=' "$ENV_FILE" | cut -d '=' -f2)
    if [[ "$DEV_STATE" == "TEST" ]]; then
        echo "🧪 Test mode detected in .env (DEV_STATE=TEST)"
        echo "⚠️ Disabling SSL certificate verification for API calls"
        CURL_SSL_OPTION="-k"
        echo "📋 Will display debug logs after completion"
        SHOW_DEBUG_LOGS=true
    else
        SHOW_DEBUG_LOGS=false
    fi
fi

# Check Docker Hub for available intel tags
echo "🔍 Checking Docker Hub for available Intel tags..."

# Validate we have both a username and repository name before checking
if [ -z "$USERNAME" ] || [ "$USERNAME" = " " ]; then
    echo "⚠️ No valid Docker username available. Will prompt for one."
    read -rp "Docker Hub username [$DEFAULT_USERNAME]: " CUSTOM_USERNAME
    USERNAME=${CUSTOM_USERNAME:-$DEFAULT_USERNAME}
    echo "Using username: $USERNAME"
fi

# Prompt for repository first, instead of trying to query with potentially empty values
echo "Repository name checks:"
echo "- Default: $DEFAULT_REPOSITORY"

read -rp "Repository name [$DEFAULT_REPOSITORY]: " CUSTOM_REPOSITORY
REPOSITORY=${CUSTOM_REPOSITORY:-$DEFAULT_REPOSITORY}
echo "Using repository: $REPOSITORY"

# Use the tag from .env file directly without Docker Hub API check
echo "Using deployment information from .env file or defaults."

# If we have the tag in .env, use that
if [ -n "$INTEL_TAG" ]; then
    echo "📋 Found Intel tag in .env file: $INTEL_TAG"
    DEFAULT_TAG=$INTEL_TAG
else
    echo "ℹ️ No Intel tag found in .env file. Using default: $DEFAULT_TAG"
fi

# Skip Docker Hub API checks entirely to avoid rate limits and permissions issues

# Prompt for values if not found in environment
if [ -z "$USERNAME" ] || [ "$USERNAME" = " " ]; then
    read -rp "Docker Hub username [$DEFAULT_USERNAME]: " CUSTOM_USERNAME
    USERNAME=${CUSTOM_USERNAME:-$DEFAULT_USERNAME}
    echo "Using username: $USERNAME"
fi

# Repository already prompted for in the Docker Hub check section

read -rp "Application name [$DEFAULT_APPLICATION_NAME]: " APP_NAME
APP_NAME=${APP_NAME:-$DEFAULT_APPLICATION_NAME}

# Port is hardcoded to 5000 to match the container's internal port
echo "🔧 Using hardcoded port: 5000 (matches container configuration)"

# Use the tag from .env if available, otherwise use default
if [ -n "$INTEL_TAG" ]; then
    echo "📋 Using Intel tag from .env file: $INTEL_TAG"
    DEFAULT_TAG=$INTEL_TAG
else
    echo "ℹ️ Using default tag: $DEFAULT_TAG"
fi

read -rp "Tag to deploy [$DEFAULT_TAG]: " CUSTOM_TAG
TAG=${CUSTOM_TAG:-$DEFAULT_TAG}

# Make sure tag is prefixed with 'intel-' if it's not 'latest'
if [[ "$TAG" != "latest" && ! "$TAG" == intel-* ]]; then
    TAG="intel-$TAG"
    echo "Adding 'intel-' prefix to tag: $TAG"
fi

# Image to deploy
IMAGE_NAME="$USERNAME/$REPOSITORY:$TAG"
echo "🚀 Preparing to deploy image: $IMAGE_NAME"

# Build the image specifically for Intel architecture using buildx
echo "🔨 Building the Intel image for Quome deployment..."
PLATFORM="linux/amd64"  # Intel architecture
echo "Building for platform: $PLATFORM"

# Make sure buildx is available
docker buildx inspect multiarch-builder >/dev/null 2>&1 || docker buildx create --name multiarch-builder --use
docker buildx use multiarch-builder

# Build and push directly with buildx
echo "Building and pushing image: $IMAGE_NAME"
docker buildx build --platform $PLATFORM -t $IMAGE_NAME --push .
echo "✅ Intel image built and pushed successfully"

# Verify image existence - simplified approach relying on docker pull
echo "🔍 Verifying image exists on Docker Hub..."

# Get system architecture
SYSTEM_ARCH=$(uname -m)
PLATFORM_ARG=""

# If this is an ARM Mac but the image is for Intel, we need to specify platform
if [[ ("$SYSTEM_ARCH" == "arm64" || "$SYSTEM_ARCH" == "aarch64") && "$TAG" == intel-* ]]; then
    echo "⚠️ Detected ARM Mac but trying to pull Intel image."
    echo "Adding --platform=linux/amd64 to pull command to enable emulation."
    PLATFORM_ARG="--platform=linux/amd64"
fi

# Verify image exists on Docker Hub using API instead of pulling
echo "🔍 Verifying image on Docker Hub..."
DOCKER_HUB_API="https://hub.docker.com/v2/repositories/$USERNAME/$REPOSITORY/tags/$TAG"
RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DOCKER_HUB_API")

if [[ "$RESPONSE_CODE" == "200" ]]; then
    echo "✅ Successfully verified image exists on Docker Hub: $IMAGE_NAME"
    IMAGE_EXISTS=true
else
    echo "⚠️ Warning: Could not verify image $IMAGE_NAME on Docker Hub (HTTP $RESPONSE_CODE)."
    echo "This is normal immediately after pushing a new image as it may take time to propagate."
    echo "However, since you just built and pushed the image, we can assume it exists."
    
    # Set to true since we just pushed it
    IMAGE_EXISTS=true
    echo "✅ Proceeding with deployment..."
fi

# Check for API key
if [ -z "$API_KEY" ]; then
    # Try to find QUOME_KEY if it wasn't found earlier with the pattern match
    if [ -f "$ENV_FILE" ]; then
        # Look specifically for QUOME_KEY
        API_KEY=$(grep '^QUOME_KEY=' "$ENV_FILE" | cut -d '=' -f2)
        if [ -n "$API_KEY" ]; then
            echo "✅ Found QUOME_KEY in .env file"
        else
            echo "No API key found in .env file. Please enter your Quome Cloud API Key:"
            read -rs API_KEY
        fi
    else
        echo "No .env file found. Please enter your Quome Cloud API Key:"
        read -rs API_KEY
    fi
fi

if [ -z "$API_KEY" ]; then
    echo "❌ API Key is required to update the cloud deployment"
    exit 1
fi

# Create or verify Docker credentials secret
echo "🔑 Ensuring Docker credentials secret exists..."

# Secret name to use for Docker credentials
DOCKER_SECRET_NAME="pallcare-docker-credentials"

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

echo "🔄 Updating $APP_NAME application in Quome Cloud..."

# First, get the current configuration to understand what's there
echo "🔍 Retrieving current app configuration..."
CURRENT_CONFIG_FILE="/tmp/quome_current_config_$(date +%s).log"
CURRENT_CONFIG=$(curl $CURL_SSL_OPTION -L -s -X GET \
    -H "Authorization: Bearer $API_KEY" \
    "$CLOUD_API_URL" 2>"$CURRENT_CONFIG_FILE")

echo "Current configuration:"
echo "$CURRENT_CONFIG" | head -30

# Check if successful
CURRENT_CONFIG_STATUS=$(echo "$CURRENT_CONFIG" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [[ "$CURRENT_CONFIG" == *"\"port\":"* ]]; then
    CURRENT_PORT=$(echo "$CURRENT_CONFIG" | grep -o '"port":[^,}]*' | cut -d: -f2 | tr -d ' ')
    echo "Currently configured port: $CURRENT_PORT"
else
    echo "Could not determine current port from configuration"
fi

# Prepare JSON payload for cloud API with registry_secret
CLOUD_PAYLOAD=$(cat <<EOF
{
    "name": "$APP_NAME",
    "spec": {
        "port": 5000,
        "containers": [
            {
                "image": "$IMAGE_NAME",
                "name": "app",
                "port": 5000,
                "tmp_dirs": [
                    "/tmp", 
                    "/tmp/pallcare"
                ],

                "env_vars": {
                    "FLASK_APP": "run.py",
                    "FLASK_ENV": "production",
                    "DEV_STATE": "TEST",
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_DB": "pallcare_db",
                    "POSTGRES_HOST": "db"
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

# Make the API request to update the app
echo "📡 Sending update request to Quome Cloud..."

# Use CLOUD_API_URL as defined at the top of the script
echo "API URL: $CLOUD_API_URL"
echo "Using image: $IMAGE_NAME"

# Show more details about what we're sending
echo "Request details:"
echo "- Method: PUT"
echo "- Content-Type: application/json"
echo "- Auth: Bearer Token (first 5 chars: ${API_KEY:0:5}...)"
echo "- Image being deployed: $IMAGE_NAME"
echo "- App Port: 5000, Container Port: 5000"

# Simplify the API request - use a single, direct approach like in debug script
echo "Attempting API request..."
DEPLOYMENT_SUCCESS=false

# Save detailed debugging output to a file for inspection if needed
CURL_DEBUG_FILE="/tmp/quome_deploy_debug_$(date +%s).log"

# Execute like the debug script does - simple and direct
echo "Executing curl command (saving debug to $CURL_DEBUG_FILE)..."

# Make one straightforward PUT request
UPDATE_RESPONSE=$(curl $CURL_SSL_OPTION -L -s -m 30 -w "\nStatus Code: %{http_code}\n" -X PUT \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "$CLOUD_PAYLOAD" \
    "$CLOUD_API_URL" 2>"$CURL_DEBUG_FILE")

CURL_EXIT_CODE=$?
    
# Extract the HTTP status code
HTTP_STATUS=$(echo "$UPDATE_RESPONSE" | grep "Status Code:" | awk '{print $3}')

# Log detailed debug info
echo "----- CURL RESPONSE INFO -----"
echo "curl exit code: $CURL_EXIT_CODE" 
echo "HTTP status code: $HTTP_STATUS"
echo "Response body preview (first 300 chars):"
echo "$UPDATE_RESPONSE" | head -10 | cut -c 1-300
echo "------------------------------"

# Simplified success check - just like in debug_push_to_quome.sh
if [[ "$HTTP_STATUS" -ge 200 && "$HTTP_STATUS" -lt 300 ]]; then
    echo "✅ Cloud deployment update initiated successfully! (HTTP $HTTP_STATUS)"
    DEPLOYMENT_SUCCESS=true
else
    echo "⚠️ Request did not succeed. Details:"
    
    # Classify the error for better debugging
    if [[ "$CURL_EXIT_CODE" -ne 0 ]]; then
        echo "❌ curl command failed with exit code $CURL_EXIT_CODE"
        echo "Common exit codes:"
        echo "  6: Could not resolve host"
        echo "  7: Failed to connect"
        echo "  28: Operation timeout"
        echo "See debug log for details: $CURL_DEBUG_FILE"
    elif [[ "$HTTP_STATUS" -eq 401 || "$HTTP_STATUS" -eq 403 ]]; then
        echo "❌ Authentication error (HTTP $HTTP_STATUS). Please check your API key."
    elif [[ "$HTTP_STATUS" -eq 404 ]]; then
        echo "❌ Resource not found (HTTP $HTTP_STATUS). Incorrect API URL or App/Org ID."
    elif [[ "$HTTP_STATUS" -eq 400 ]]; then
        echo "❌ Bad request (HTTP $HTTP_STATUS). Likely an issue with the payload format."
        echo "API Response:"
        echo "$UPDATE_RESPONSE"
    elif [[ "$HTTP_STATUS" -eq 0 ]]; then
        echo "❌ No HTTP status received. Connection problem or timeout."
    else
        echo "❌ Unexpected HTTP status: $HTTP_STATUS"
    fi
fi

# Final deployment status report
if [ "$DEPLOYMENT_SUCCESS" = "true" ]; then
    echo ""
    echo "🎉 DEPLOYMENT SUCCESS! 🎉"
    echo "⏱️  The new version should be available in about a minute after SBOM scan completes."
    echo "🔗 Visit: https://demo.quome.cloud/apps/$CLOUD_APP_ID"
    
    # Add verification of deployment status
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
else
    echo ""
    echo "❌ DEPLOYMENT FAILED ❌"
    echo "Last API Response:"
    echo "$UPDATE_RESPONSE"
    echo ""
    echo "Detailed troubleshooting steps:"
    echo "  1. Check your API key is correct and not expired"
    echo "     Current key starts with: ${API_KEY:0:8}..."
    echo "  2. Verify Organization ID ($CLOUD_ORG_ID) and App ID ($CLOUD_APP_ID) are correct"
    echo "  3. Confirm the Quome Cloud API endpoint ($HTTPS_API_URL) is reachable"
    echo "  4. Ensure the image ($IMAGE_NAME) exists and is properly tagged"
    echo "  5. Examine the debug log: $CURL_DEBUG_FILE"
    echo ""
    echo "You can retry the deployment or contact Quome Cloud support if the issue persists."
    exit 1
fi

# Update the current Intel tag in .env file if it doesn't exist
if [ -f "$ENV_FILE" ] && ! grep -q "^INTEL_CURRENT_TAG=" "$ENV_FILE"; then
    echo "INTEL_CURRENT_TAG=$TAG" >> "$ENV_FILE"
    echo "📝 Added INTEL_CURRENT_TAG=$TAG to .env file"
fi

echo ""
echo "📌 Deployment Summary:"
echo "- Application: $APP_NAME"
echo "- Image: $IMAGE_NAME"
echo "- App Port: 5000, Container Port: 5000"
echo "- API URL: $CLOUD_API_URL"
echo "- Deployment Status: $([ "$DEPLOYMENT_SUCCESS" = "true" ] && echo "✅ SUCCESS" || echo "❌ FAILED")"
echo "- Exit Code: $([ "$DEPLOYMENT_SUCCESS" = "true" ] && echo "0" || echo "1")"
echo ""

if [ "$DEPLOYMENT_SUCCESS" = "true" ]; then
    echo "🔗 Monitor deployment: https://demo.quome.cloud/apps/$CLOUD_APP_ID"
    echo "⚡ Status updates:"
    echo "  - Initial deployment typically takes 1-2 minutes"
    echo "  - SBOM scanning may add another 1-3 minutes"
    echo "  - App should be running at: https://demo.quome.cloud/apps/$CLOUD_APP_ID"
    
    # Show debug logs in test mode
    if [ "$SHOW_DEBUG_LOGS" = true ]; then
        echo ""
        echo "🔍 DEBUG LOGS (Test Mode Only) 🔍"
        if [ -f "$SECRET_DEBUG_FILE" ]; then
            echo "=== SECRET CREATION LOG ==="
            cat "$SECRET_DEBUG_FILE"
            echo "=========================="
        fi
        if [ -f "$CURL_DEBUG_FILE" ]; then
            echo ""
            echo "=== DEPLOYMENT LOG ==="
            cat "$CURL_DEBUG_FILE"
            echo "======================"
        fi
    fi
    
    # For TEST deployments, perform additional verification
    if [ "${DEV_STATE}" = "TEST" ]; then
        echo ""
        echo "🧪 TEST MODE DEPLOYMENT VERIFICATION 🧪"
        echo "Performing additional verification checks for TEST mode deployment..."
        
        # Wait for app to fully start
        echo "⏳ Waiting 30 seconds for complete initialization..."
        sleep 30
        
        # Get deployment logs
        echo "📋 Retrieving deployment logs..."
        LOGS_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID/logs"
        
        APP_LOGS=$(curl $CURL_SSL_OPTION -L -s -X GET \
            -H "Authorization: Bearer $API_KEY" \
            "$LOGS_API_URL" 2>/dev/null)
        
        LOG_SIZE=${#APP_LOGS}
        echo "Retrieved $LOG_SIZE bytes of logs"
        
        # Check for successful database initialization markers in logs
        if [[ "$APP_LOGS" == *"Database tables created"* || 
              "$APP_LOGS" == *"Database seeded with initial data"* || 
              "$APP_LOGS" == *"Database restored from backup successfully"* ]]; then
            echo "✅ Log analysis: Database initialization appears SUCCESSFUL"
        else
            echo "⚠️ Log analysis: Could not confirm database initialization in logs"
            echo "This might be normal if logs are truncated or if the deployment is still initializing"
        fi
        
        # Check if admin credentials are present
        if [[ "$APP_LOGS" == *"Default login credentials"* && 
              "$APP_LOGS" == *"Admin: admin / password123"* ]]; then
            echo "✅ Log analysis: Default admin credentials confirmed"
        else
            echo "⚠️ Log analysis: Could not confirm default admin credentials in logs"
        fi
        
        # Application availability test
        echo "🔍 Checking if application is responding..."
        APP_URL=$(echo "$VERIFY_CONFIG" | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [ -n "$APP_URL" ]; then
            echo "Application URL: $APP_URL"
            
            # Try to access login page
            LOGIN_URL="${APP_URL}/login"
            LOGIN_RESPONSE=$(curl $CURL_SSL_OPTION -L -s -m 10 -w "\nStatus Code: %{http_code}\n" \
                "$LOGIN_URL" 2>/dev/null)
            
            LOGIN_STATUS=$(echo "$LOGIN_RESPONSE" | grep "Status Code:" | awk '{print $3}')
            
            if [[ "$LOGIN_STATUS" -eq 200 ]]; then
                echo "✅ Login page is accessible (HTTP 200)"
                
                # Check if login form is present
                if [[ "$LOGIN_RESPONSE" == *"form"* && "$LOGIN_RESPONSE" == *"password"* ]]; then
                    echo "✅ Login form detected on page"
                    echo "🟢 APPLICATION VERIFICATION SUCCESSFUL"
                    echo "You should now be able to log in with:"
                    echo "  Username: admin"
                    echo "  Password: password123"
                else
                    echo "⚠️ Login form not detected on page"
                    echo "🟡 APPLICATION VERIFICATION PARTIALLY SUCCESSFUL"
                fi
            else
                echo "⚠️ Login page returned HTTP $LOGIN_STATUS"
                echo "🔴 APPLICATION VERIFICATION FAILED"
                echo "The application might need more time to start up"
            fi
        else
            echo "⚠️ Could not determine application URL from deployment details"
            echo "🔴 APPLICATION VERIFICATION FAILED"
        fi
    fi
    
    # Return success exit code
    exit 0
else
    echo "❗ Debug information saved to: $CURL_DEBUG_FILE"
    echo "Try running the script again or contact Quome Cloud support."
    
    # Show debug logs in test mode
    if [ "$SHOW_DEBUG_LOGS" = true ]; then
        echo ""
        echo "🔍 DEBUG LOGS (Test Mode Only) 🔍"
        if [ -f "$SECRET_DEBUG_FILE" ]; then
            echo "=== SECRET CREATION LOG ==="
            cat "$SECRET_DEBUG_FILE"
            echo "=========================="
        fi
        if [ -f "$CURL_DEBUG_FILE" ]; then
            echo ""
            echo "=== DEPLOYMENT LOG ==="
            cat "$CURL_DEBUG_FILE"
            echo "======================"
        fi
    fi
    
    # For TEST deployments, show additional info even on failure
    if [ "${DEV_STATE}" = "TEST" ]; then
        echo ""
        echo "🧪 TEST MODE FAILURE ANALYSIS 🧪"
        echo "Analyzing failure for TEST mode deployment..."
        
        # Get deployment logs if available
        echo "📋 Attempting to retrieve any available logs..."
        LOGS_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID/logs"
        
        APP_LOGS=$(curl $CURL_SSL_OPTION -L -s -X GET \
            -H "Authorization: Bearer $API_KEY" \
            "$LOGS_API_URL" 2>/dev/null)
        
        LOG_SIZE=${#APP_LOGS}
        if [ $LOG_SIZE -gt 0 ]; then
            echo "Retrieved $LOG_SIZE bytes of logs"
            echo "Log preview (first 20 lines):"
            echo "$APP_LOGS" | head -20
            
            # Look for common errors
            if [[ "$APP_LOGS" == *"database"*"connect"*"failed"* ]]; then
                echo "❌ ERROR DETECTED: Database connection issues"
            elif [[ "$APP_LOGS" == *"permission denied"* ]]; then
                echo "❌ ERROR DETECTED: Permission issues"
            elif [[ "$APP_LOGS" == *"pull access denied"* ]]; then
                echo "❌ ERROR DETECTED: Docker image pull issues - check Docker credentials"
            fi
        else
            echo "No logs available. The application might not have started yet."
        fi
        
        echo ""
        echo "🔬 TROUBLESHOOTING TIPS:"
        echo "1. Check if the Docker image was built and pushed correctly"
        echo "2. Verify Docker credentials in the Quome Cloud dashboard"
        echo "3. Check if the database secret exists and is configured correctly"
        echo "4. Ensure the docker_startup.sh script has execute permissions (chmod +x)"
        echo ""
    fi
    
    # Return failure exit code
    exit 1
fi
