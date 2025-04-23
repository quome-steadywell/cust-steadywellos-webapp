#!/bin/bash
# push_to_quome.sh - Update cloud deployment for palliative care app using the latest Intel image
#
# Usage:
#   ./push_to_quome.sh           - Deploy the application to Quome Cloud
#   ./push_to_quome.sh --logs    - Fetch and display application logs from Quome Cloud
#   ./push_to_quome.sh --logs --watch    - Continuously monitor application logs
#   ./push_to_quome.sh --diagnose        - Run diagnostic tools for deployment issues
#   ./push_to_quome.sh --debug           - Show detailed debugging information

set -e  # Exit on error

# Set color codes for prettier output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Required values - will be loaded from .env file
DEFAULT_USERNAME=""
DEFAULT_REPOSITORY=""
DEFAULT_APPLICATION_NAME=""
DEFAULT_PORT=""
DEFAULT_CONTAINER_PORT=""
CLOUD_ORG_ID=""
CLOUD_APP_ID=""
# URLs will be constructed after loading values from .env
DEBUG_MODE=true

# Get script directory and environment file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"
USERNAME=""
DOCKER_TOKEN=""
DOCKER_PASSWORD=""
API_KEY=""
CURL_SSL_OPTION="-k"  # Always disable SSL verification

# Detect architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
    ARCH_PREFIX="arm"
    HOST_ARCH="arm64"
    echo -e "${BLUE}🖥️  Detected ARM architecture${NC}"
else
    ARCH_PREFIX="intel"
    HOST_ARCH="amd64"
    echo -e "${BLUE}🖥️  Detected Intel/AMD architecture${NC}"
fi

# Default tag based on architecture
DEFAULT_TAG="${ARCH_PREFIX}-0.0.1"

# Function to parse current tag and increment version
increment_tag() {
    local current_tag=$1
    local arch_prefix=$2

    # Extract version numbers, ignoring architecture prefix
    if [[ $current_tag =~ ${arch_prefix}-([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
        local major=${BASH_REMATCH[1]}
        local minor=${BASH_REMATCH[2]}
        local patch=${BASH_REMATCH[3]}

        # Increment patch version
        patch=$((patch + 1))
        echo "${arch_prefix}-$major.$minor.$patch"
    else
        # If tag doesn't match expected format, use default
        echo "${arch_prefix}-0.0.2"
    fi
}

# Load as many values as possible from .env file
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ ERROR: .env file not found at $ENV_FILE${NC}"
    echo -e "${RED}Please create a .env file with the required values:${NC}"
    echo -e "${YELLOW}DEFAULT_USERNAME=your_username${NC}"
    echo -e "${YELLOW}DEFAULT_REPOSITORY=your_repository${NC}"
    echo -e "${YELLOW}DEFAULT_APPLICATION_NAME=your_app_name${NC}"
    echo -e "${YELLOW}CLOUD_ORG_ID=your_org_id${NC}"
    echo -e "${YELLOW}CLOUD_APP_ID=your_app_id${NC}"
    exit 1
else
    echo -e "${BLUE}📋 Loading configuration from .env file...${NC}"

    # Basic configuration
    ENV_USERNAME=$(grep '^DOCKER_USERNAME=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$ENV_USERNAME" ]; then
        # Strip quotes if present
        USERNAME=$(echo "$ENV_USERNAME" | sed -e 's/^"//' -e 's/"$//')
        DEFAULT_USERNAME=$USERNAME
        echo -e "${GREEN}✅ Using Docker username: $USERNAME from .env file${NC}"
    fi

    # Repository name
    ENV_REPOSITORY=$(grep '^DEFAULT_REPOSITORY=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$ENV_REPOSITORY" ]; then
        # Strip quotes if present
        DEFAULT_REPOSITORY=$(echo "$ENV_REPOSITORY" | sed -e 's/^"//' -e 's/"$//')
        echo -e "${GREEN}✅ Using repository name from .env file: $DEFAULT_REPOSITORY${NC}"
    fi

    # Application name
    ENV_APP_NAME=$(grep '^DEFAULT_APPLICATION_NAME=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$ENV_APP_NAME" ]; then
        # Strip quotes if present
        DEFAULT_APPLICATION_NAME=$(echo "$ENV_APP_NAME" | sed -e 's/^"//' -e 's/"$//')
        echo -e "${GREEN}✅ Using application name from .env file: $DEFAULT_APPLICATION_NAME${NC}"
    fi

    # Port configuration
    ENV_PORT=$(grep '^DEFAULT_PORT=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$ENV_PORT" ]; then
        # Strip quotes if present
        DEFAULT_PORT=$(echo "$ENV_PORT" | sed -e 's/^"//' -e 's/"$//')
        echo -e "${GREEN}✅ Using port from .env file: $DEFAULT_PORT${NC}"
    fi

    # Container port
    ENV_CONTAINER_PORT=$(grep '^DEFAULT_CONTAINER_PORT=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$ENV_CONTAINER_PORT" ]; then
        # Strip quotes if present
        DEFAULT_CONTAINER_PORT=$(echo "$ENV_CONTAINER_PORT" | sed -e 's/^"//' -e 's/"$//')
        echo -e "${GREEN}✅ Using container port from .env file: $DEFAULT_CONTAINER_PORT${NC}"
    fi

    # Cloud org ID
    ENV_CLOUD_ORG_ID=$(grep '^CLOUD_ORG_ID=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$ENV_CLOUD_ORG_ID" ]; then
        # Strip quotes if present
        CLOUD_ORG_ID=$(echo "$ENV_CLOUD_ORG_ID" | sed -e 's/^"//' -e 's/"$//')
        echo -e "${GREEN}✅ Using Cloud Organization ID from .env file${NC}"
    fi

    # Cloud app ID
    ENV_CLOUD_APP_ID=$(grep '^CLOUD_APP_ID=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$ENV_CLOUD_APP_ID" ]; then
        # Strip quotes if present
        CLOUD_APP_ID=$(echo "$ENV_CLOUD_APP_ID" | sed -e 's/^"//' -e 's/"$//')
        echo -e "${GREEN}✅ Using Cloud App ID from .env file${NC}"
    fi

    # Docker token
    if grep -q '^DOCKER_TOKEN=' "$ENV_FILE"; then
        DOCKER_TOKEN=$(grep '^DOCKER_TOKEN=' "$ENV_FILE" | cut -d '=' -f2)
        # Strip quotes if present
        DOCKER_TOKEN=$(echo "$DOCKER_TOKEN" | sed -e 's/^"//' -e 's/"$//')
        if [ -z "$DOCKER_TOKEN" ]; then
            echo -e "${YELLOW}⚠️ DOCKER_TOKEN found in .env file but appears to be empty${NC}"
        else
            echo -e "${GREEN}✅ Found DOCKER_TOKEN in .env file${NC}"
        fi
    fi

    # Docker password (if available)
    DOCKER_PASSWORD=$(grep '^DOCKER_PASSWORD=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$DOCKER_PASSWORD" ]; then
        # Strip quotes if present
        DOCKER_PASSWORD=$(echo "$DOCKER_PASSWORD" | sed -e 's/^"//' -e 's/"$//')
        echo -e "${GREEN}✅ Found DOCKER_PASSWORD in .env file${NC}"
    fi

    # ANTHROPIC_API_KEY (if available)
    ANTHROPIC_API_KEY=$(grep '^ANTHROPIC_API_KEY=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        # Strip quotes if present
        ANTHROPIC_API_KEY=$(echo "$ANTHROPIC_API_KEY" | sed -e 's/^"//' -e 's/"$//')
        echo -e "${GREEN}✅ Found ANTHROPIC_API_KEY in .env file${NC}"
    fi

    # Get API key - try all possible env var names
    API_KEY=$(grep -E '^(CLOUD_API_KEY|QUOME_KEY|QUOME_API_KEY)=' "$ENV_FILE" | head -1 | cut -d '=' -f2)
    if [ -n "$API_KEY" ]; then
        # Strip quotes if present
        API_KEY=$(echo "$API_KEY" | sed -e 's/^"//' -e 's/"$//')
        echo -e "${GREEN}✅ Found API key in .env file${NC}"
        if [ "$DEBUG_MODE" = true ]; then
            echo "Debug: API key (first 8 chars): ${API_KEY:0:8}..."
        fi
    fi

    # Get latest Intel tag
    INTEL_TAG=$(grep '^INTEL_CURRENT_TAG=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$INTEL_TAG" ]; then
        # Strip quotes if present
        INTEL_TAG=$(echo "$INTEL_TAG" | sed -e 's/^"//' -e 's/"$//')
        # Increment the current tag
        DEFAULT_TAG=$(increment_tag "$INTEL_TAG" "intel")
        echo -e "${GREEN}✅ Using incrementally updated tag: $DEFAULT_TAG based on $INTEL_TAG from .env file${NC}"
    else
        DEFAULT_TAG="${ARCH_PREFIX}-0.0.1"
        echo -e "${YELLOW}ℹ️ No Intel tag found in .env file. Using default: $DEFAULT_TAG${NC}"
    fi

    # Check DEV_STATE for testing mode
    DEV_STATE=$(grep '^DEV_STATE=' "$ENV_FILE" | cut -d '=' -f2)
    if [[ "$DEV_STATE" == "TEST" ]]; then
        echo -e "${YELLOW}🧪 Test mode detected in .env (DEV_STATE=TEST)${NC}"
        echo -e "${BLUE}📋 Will display debug logs after completion${NC}"
        SHOW_DEBUG_LOGS=true
        # Enable debug mode in test environment
        DEBUG_MODE=true
    else
        SHOW_DEBUG_LOGS=false
    fi
fi

# Construct API URLs with loaded values
CLOUD_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID"
CLOUD_LOGS_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID/logs"

echo -e "${BLUE}ℹ️ SSL certificate verification disabled (using -k option)${NC}"

# Check for required values and prompt if missing
if [ -z "$DEFAULT_USERNAME" ]; then
    read -rp "Docker Hub username: " DEFAULT_USERNAME
    if [ -z "$DEFAULT_USERNAME" ]; then
        echo -e "${RED}❌ Docker username is required${NC}"
        exit 1
    fi
    USERNAME=$DEFAULT_USERNAME
fi

if [ -z "$DEFAULT_REPOSITORY" ]; then
    read -rp "Repository name: " DEFAULT_REPOSITORY
    if [ -z "$DEFAULT_REPOSITORY" ]; then
        echo -e "${RED}❌ Repository name is required${NC}"
        exit 1
    fi
fi

if [ -z "$DEFAULT_APPLICATION_NAME" ]; then
    read -rp "Application name: " DEFAULT_APPLICATION_NAME
    if [ -z "$DEFAULT_APPLICATION_NAME" ]; then
        echo -e "${RED}❌ Application name is required${NC}"
        exit 1
    fi
fi

# Use default port if not specified
if [ -z "$DEFAULT_PORT" ]; then
    DEFAULT_PORT="8080"
    echo -e "${YELLOW}⚠️ Using default port: $DEFAULT_PORT${NC}"
fi

# Use default container port if not specified
if [ -z "$DEFAULT_CONTAINER_PORT" ]; then
    DEFAULT_CONTAINER_PORT="5000"
    echo -e "${YELLOW}⚠️ Using default container port: $DEFAULT_CONTAINER_PORT${NC}"
fi

# Check Docker Hub for available intel tags
echo -e "${BLUE}🔍 Checking Docker Hub for available Intel tags...${NC}"

# Prompt for repository first, instead of trying to query with potentially empty values
echo "Repository name checks:"
echo "- Default: $DEFAULT_REPOSITORY"

read -rp "Repository name [$DEFAULT_REPOSITORY]: " CUSTOM_REPOSITORY
REPOSITORY=${CUSTOM_REPOSITORY:-$DEFAULT_REPOSITORY}
echo -e "${GREEN}✅ Using repository: $REPOSITORY${NC}"

# Use the tag from .env file directly without Docker Hub API check
echo -e "${BLUE}Using deployment information from .env file or defaults.${NC}"

# If we have the tag in .env, use that
if [ -n "$INTEL_TAG" ]; then
    echo -e "${GREEN}📋 Found Intel tag in .env file: $INTEL_TAG${NC}"
    DEFAULT_TAG=$INTEL_TAG
else
    echo -e "${YELLOW}ℹ️ No Intel tag found in .env file. Using default: $DEFAULT_TAG${NC}"
fi

# Skip Docker Hub API checks entirely to avoid rate limits and permissions issues

# Prompt for values if not found in environment
if [ -z "$USERNAME" ] || [ "$USERNAME" = " " ]; then
    read -rp "Docker Hub username [$DEFAULT_USERNAME]: " CUSTOM_USERNAME
    USERNAME=${CUSTOM_USERNAME:-$DEFAULT_USERNAME}
    echo -e "${GREEN}✅ Using username: $USERNAME${NC}"
fi

# Repository already prompted for above

read -rp "Application name [$DEFAULT_APPLICATION_NAME]: " APP_NAME
APP_NAME=${APP_NAME:-$DEFAULT_APPLICATION_NAME}

# Port is hardcoded to 5000 to match the container's internal port
echo -e "${BLUE}🔧 Using hardcoded port: 5000 (matches container configuration)${NC}"

# Use the tag from .env if available, otherwise use default
if [ -n "$INTEL_TAG" ]; then
    echo -e "${GREEN}📋 Using Intel tag from .env file: $INTEL_TAG${NC}"
    DEFAULT_TAG=$INTEL_TAG
else
    echo -e "${YELLOW}ℹ️ Using default tag: $DEFAULT_TAG${NC}"
fi

read -rp "Tag to deploy [$DEFAULT_TAG]: " CUSTOM_TAG
TAG=${CUSTOM_TAG:-$DEFAULT_TAG}

# Make sure tag is prefixed with 'intel-' if it's not 'latest'
if [[ "$TAG" != "latest" && ! "$TAG" == intel-* ]]; then
    TAG="intel-$TAG"
    echo -e "${YELLOW}Adding 'intel-' prefix to tag: $TAG${NC}"
fi

# Image to deploy
IMAGE_NAME="$USERNAME/$REPOSITORY:$TAG"
echo -e "${BLUE}🚀 Preparing to deploy image: $IMAGE_NAME${NC}"

# Build the image specifically for Intel architecture using buildx
echo -e "${BLUE}🔨 Building the Intel image for Quome deployment...${NC}"
PLATFORM="linux/amd64"  # Intel architecture
echo "Building for platform: $PLATFORM"

# Make sure buildx is available
docker buildx inspect multiarch-builder >/dev/null 2>&1 || docker buildx create --name multiarch-builder --use
docker buildx use multiarch-builder

# Build and push directly with buildx
echo "Building and pushing image: $IMAGE_NAME"
docker buildx build --platform $PLATFORM -t $IMAGE_NAME --push .
echo -e "${GREEN}✅ Intel image built and pushed successfully${NC}"

# Verify image existence - simplified approach relying on docker pull
echo -e "${BLUE}🔍 Verifying image exists on Docker Hub...${NC}"

# Get system architecture
SYSTEM_ARCH=$(uname -m)
PLATFORM_ARG=""

# If this is an ARM Mac but the image is for Intel, we need to specify platform
if [[ ("$SYSTEM_ARCH" == "arm64" || "$SYSTEM_ARCH" == "aarch64") && "$TAG" == intel-* ]]; then
    echo -e "${YELLOW}⚠️ Detected ARM Mac but trying to pull Intel image.${NC}"
    echo "Adding --platform=linux/amd64 to pull command to enable emulation."
    PLATFORM_ARG="--platform=linux/amd64"
fi

# Verify image exists on Docker Hub using API instead of pulling
echo -e "${BLUE}🔍 Verifying image on Docker Hub...${NC}"
DOCKER_HUB_API="https://hub.docker.com/v2/repositories/$USERNAME/$REPOSITORY/tags/$TAG"
RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DOCKER_HUB_API")

if [[ "$RESPONSE_CODE" == "200" ]]; then
    echo -e "${GREEN}✅ Successfully verified image exists on Docker Hub: $IMAGE_NAME${NC}"
    IMAGE_EXISTS=true
else
    echo -e "${YELLOW}⚠️ Warning: Could not verify image $IMAGE_NAME on Docker Hub (HTTP $RESPONSE_CODE).${NC}"
    echo "This is normal immediately after pushing a new image as it may take time to propagate."
    echo "However, since you just built and pushed the image, we can assume it exists."

    # Set to true since we just pushed it
    IMAGE_EXISTS=true
    echo -e "${GREEN}✅ Proceeding with deployment...${NC}"
fi

# Check for API key
if [ -z "$API_KEY" ]; then
    # Try to find QUOME_KEY if it wasn't found earlier with the pattern match
    if [ -f "$ENV_FILE" ]; then
        # Look specifically for QUOME_KEY
        API_KEY=$(grep '^QUOME_KEY=' "$ENV_FILE" | cut -d '=' -f2)
        if [ -n "$API_KEY" ]; then
            echo -e "${GREEN}✅ Found QUOME_KEY in .env file${NC}"
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
    echo -e "${RED}❌ API Key is required to update the cloud deployment${NC}"
    exit 1
fi

# Create or verify Docker credentials secret
echo "🔑 Ensuring Docker credentials secret exists..."

# Secret name to use for Docker credentials
DOCKER_SECRET_NAME="pallcare-docker-credentials"

# Create Docker credentials secret with proper payload structure
if [ -n "$DOCKER_TOKEN" ]; then
    DOCKER_SECRET_PAYLOAD=$(cat <<EOF
{
    "name": "pallcare-docker-credentials",
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

    # Debug: Show Docker secret payload if debug mode is enabled
    if [ "$DEBUG_MODE" = true ]; then
        echo -e "${BLUE}Debug: DOCKER_SECRET_PAYLOAD:${NC}"
        echo "$DOCKER_SECRET_PAYLOAD" | jq . 2>/dev/null || echo "$DOCKER_SECRET_PAYLOAD"
        echo ""
    fi
fi

# Create or verify Anthropic Key secret
echo "🔑 Ensuring Anthropic Key secret exists..."

# Secret name to use for Anthropic Key
ANTHROPIC_SECRET_NAME="anthropic-key"

# Create Docker credentials secret with proper payload structure
if [ -n "$ANTHROPIC_API_KEY" ]; then
    ANTHROPIC_SECRET_PAYLOAD=$(cat <<EOF
{
    "name": "anthropic-key",
    "type": "generic",
    "description": "anthropic api key",
    "secret": {
        "key": "$ANTHROPIC_API_KEY"
    }
}
EOF
)

    # Debug: Show Docker secret payload if debug mode is enabled
    if [ "$DEBUG_MODE" = true ]; then
        echo -e "${BLUE}Debug: ANTHROPIC_SECRET_PAYLOAD:${NC}"
        echo "$ANTHROPIC_SECRET_PAYLOAD" | jq . 2>/dev/null || echo "$ANTHROPIC_SECRET_PAYLOAD"
        echo ""
    fi
fi

# Function to check app status and provide useful information
check_app_status() {
    echo -e "${BLUE}Checking application status...${NC}"
    APP_STATUS=$(curl $CURL_SSL_OPTION -L -s -X GET \
        -H "Authorization: Bearer $API_KEY" \
        "$CLOUD_API_URL" 2>/dev/null)

    if [ -n "$APP_STATUS" ]; then
        if [ "$DEBUG_MODE" = true ]; then
            echo "Debug: App status response:"
            echo "$APP_STATUS" | jq . 2>/dev/null || echo "$APP_STATUS"
        fi

        # Extract key information
        APP_NAME=$(echo "$APP_STATUS" | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4)
        APP_STATE=$(echo "$APP_STATUS" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [ -z "$APP_STATE" ]; then
            APP_STATE=$(echo "$APP_STATUS" | grep -o '"state":"[^"]*"' | head -1 | cut -d'"' -f4)
        fi
        APP_HEALTH=$(echo "$APP_STATUS" | grep -o '"health":"[^"]*"' | head -1 | cut -d'"' -f4)
        DEPLOYMENT_TIME=$(echo "$APP_STATUS" | grep -o '"created_at":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [ -z "$DEPLOYMENT_TIME" ]; then
            DEPLOYMENT_TIME=$(echo "$APP_STATUS" | grep -o '"created":"[^"]*"' | head -1 | cut -d'"' -f4)
        fi

        # Format the timestamp for better readability if available
        if [ -n "$DEPLOYMENT_TIME" ]; then
            DEPLOYMENT_TIME_FORMATTED=$(date -d "$DEPLOYMENT_TIME" "+%Y-%m-%d %H:%M:%S" 2>/dev/null)
            if [ $? -eq 0 ]; then
                DEPLOYMENT_TIME="$DEPLOYMENT_TIME_FORMATTED"
            fi
        fi

        echo -e "${YELLOW}Application: ${NC}$APP_NAME"
        echo -e "${YELLOW}Status: ${NC}$APP_STATE"
        [ -n "$APP_HEALTH" ] && echo -e "${YELLOW}Health: ${NC}$APP_HEALTH"
        [ -n "$DEPLOYMENT_TIME" ] && echo -e "${YELLOW}Deployed at: ${NC}$DEPLOYMENT_TIME"

        if [[ "$APP_STATE" == "running" || "$APP_HEALTH" == "healthy" ]]; then
            echo -e "${GREEN}Application is currently running${NC}"
        elif [[ "$APP_STATE" == "deploying" ]]; then
            echo -e "${YELLOW}Application is currently being deployed${NC}"
            echo "Logs will be available once deployment completes."
        elif [[ "$APP_STATE" == "error" || "$APP_STATE" == "failed" || "$APP_HEALTH" == "down" ]]; then
            echo -e "${RED}Application is in an error state${NC}"
            # Try to extract error message
            ERROR_MSG=$(echo "$APP_STATUS" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
            ERROR_MSG2=$(echo "$APP_STATUS" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
            if [ -n "$ERROR_MSG" ]; then
                echo "Error message: $ERROR_MSG"
            elif [ -n "$ERROR_MSG2" ]; then
                echo "Error message: $ERROR_MSG2"
            else
                echo "No specific error message available."
            fi
        else
            echo -e "${YELLOW}Application has unknown status: $APP_STATE${NC}"
        fi

        # Attempt to extract container info
        CONTAINERS=$(echo "$APP_STATUS" | grep -o '"containers":\[[^]]*\]' | sed 's/"containers"://g')
        if [ -n "$CONTAINERS" ]; then
            CONTAINER_COUNT=$(echo "$CONTAINERS" | grep -o '"name"' | wc -l)
            echo "Deployment has $CONTAINER_COUNT container(s)"

            # Extract image info
            IMAGES=$(echo "$APP_STATUS" | grep -o '"image":"[^"]*"' | cut -d'"' -f4)
            if [ -n "$IMAGES" ]; then
                echo -e "${YELLOW}Container images:${NC}"
                echo "$IMAGES" | while read -r IMAGE; do
                    echo "  - $IMAGE"
                done
            fi
        fi
    else
        echo -e "${RED}Could not retrieve application status${NC}"
        echo "Please check your API key and network connection."
    fi

    echo ""
    echo "Check the app dashboard at: https://demo.quome.cloud/apps/$CLOUD_APP_ID"
}

# Function to fetch and display logs
fetch_logs() {
    echo -e "${BLUE}📋 Fetching application logs from Quome Cloud...${NC}"

    # Debug info
    if [ "$DEBUG_MODE" = true ]; then
        echo "Debug: CLOUD_LOGS_URL = $CLOUD_LOGS_URL"
        echo "Debug: API Key prefix = ${API_KEY:0:5}..."
        echo "Debug: Curl SSL Option = $CURL_SSL_OPTION"
    fi

    # Create a temporary file to capture curl stderr
    CURL_ERROR_FILE="/tmp/quome_curl_error_$(date +%s).log"

    # Fetch logs with curl - added -v for verbose output in debug mode
    CURL_OPTS="-L -s"
    [ "$DEBUG_MODE" = true ] && CURL_OPTS="-L -v"

    if [ "$DEBUG_MODE" = true ]; then
        echo "Debug: Executing curl $CURL_SSL_OPTION $CURL_OPTS -X GET -H \"Authorization: Bearer ***\" \"$CLOUD_LOGS_URL\""
    fi

    # Set these as global variables so they can be used outside the function
    APP_LOGS=$(curl $CURL_SSL_OPTION $CURL_OPTS -X GET \
        -H "Authorization: Bearer $API_KEY" \
        "$CLOUD_LOGS_URL" 2>$CURL_ERROR_FILE)

    CURL_EXIT_CODE=$?
    LOG_SIZE=${#APP_LOGS}

    if [ "$DEBUG_MODE" = true ]; then
        echo "Debug: curl exit code = $CURL_EXIT_CODE"
        echo "Debug: Log size = $LOG_SIZE bytes"
        echo "Debug: curl error output:"
        cat $CURL_ERROR_FILE
    fi

    if [ $CURL_EXIT_CODE -ne 0 ]; then
        echo -e "${RED}Curl command failed with exit code $CURL_EXIT_CODE${NC}"
        echo "Error details:"
        cat $CURL_ERROR_FILE
        return 1
    fi

    if [ $LOG_SIZE -gt 0 ]; then
        echo -e "${GREEN}Retrieved $LOG_SIZE bytes of logs${NC}"

        # Check if response is JSON error instead of logs
        if [[ "$APP_LOGS" == *"\"error\""* || "$APP_LOGS" == *"\"status\":\"error\""* ]]; then
            echo -e "${RED}Received error response from API:${NC}"
            echo "$APP_LOGS"
            return 1
        fi

        # Check if the response is an empty array - common when no logs available
        if [[ "$APP_LOGS" == "[]" ]]; then
            echo -e "${YELLOW}No logs available - API returned empty array []${NC}"
            check_app_status
            return 0
        fi

        echo -e "${BLUE}========================== APPLICATION LOGS ==========================${NC}"
        # Use printf to interpret escape sequences like \n for line breaks
        printf "%b\n" "$APP_LOGS"
        echo -e "${BLUE}====================================================================${NC}"

        # Save logs to a file for reference
        LOG_FILE="/tmp/quome_app_logs_$(date +%s).log"
        echo "$APP_LOGS" > "$LOG_FILE"
        echo -e "${GREEN}Full logs saved to: $LOG_FILE${NC}"
        return 0
    else
        echo -e "${RED}No logs retrieved from $CLOUD_LOGS_URL${NC}"
        echo -e "${YELLOW}Possible issues:${NC}"
        echo "  1. The application may not be deployed or running"
        echo "  2. The API key may be incorrect or expired"
        echo "  3. The Organization ID or App ID may be incorrect"
        echo "  4. There might be a network connectivity issue"

        # Check app status to provide more info
        check_app_status

        return 1
    fi
}

# Process command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --logs|-l) LOGS_MODE=true; shift ;;
        --watch|-w) WATCH_MODE=true; shift ;;
        --debug|-d) DEBUG_MODE=true; shift ;;
        --diagnose) DIAGNOSE_MODE=true; shift ;;
        --interval) INTERVAL="$2"; shift 2 ;;
        *)
            if [[ "$WATCH_MODE" == "true" && "$1" =~ ^[0-9]+$ ]]; then
                INTERVAL="$1"; shift
            else
                echo -e "${RED}Unknown parameter: $1${NC}"; exit 1
            fi
            ;;
    esac
done

# Set default interval if not specified
INTERVAL=${INTERVAL:-10}

# Add a command-line option to just fetch logs
if [ "$LOGS_MODE" = "true" ]; then
    # Make sure we have an API key
    if [ -z "$API_KEY" ]; then
        echo -e "${RED}No API key found. Please check your .env file or provide the key manually.${NC}"
        exit 1
    fi

    echo -e "${BLUE}Log-only mode activated. Fetching logs for app ID: $CLOUD_APP_ID${NC}"

    if [ "$WATCH_MODE" = "true" ]; then
        echo -e "${BLUE}📺 Watching logs with $INTERVAL second refresh interval. Press Ctrl+C to exit.${NC}"

        while true; do
            clear
            echo -e "${BLUE}🕒 Refreshing logs at $(date)${NC}"
            fetch_logs
            echo ""
            echo -e "${YELLOW}Will refresh in $INTERVAL seconds... (Press Ctrl+C to exit)${NC}"
            sleep $INTERVAL
        done
    else
        fetch_logs
    fi
    exit $?
fi

if [ "$DIAGNOSE_MODE" = "true" ]; then
    echo -e "${BLUE}🔍 Running diagnostic tools for Quome Cloud deployment issues...${NC}"
    check_app_status
    exit 0
fi

# Check if Docker token is available
if [ -z "$DOCKER_TOKEN" ]; then
    echo -e "${YELLOW}⚠️ Docker token not found in .env file${NC}"
    echo "Skipping Docker credentials secret creation."
    echo "The existing secret '$DOCKER_SECRET_NAME' will be used if available."
else
    # Create Docker credentials secret
    echo -e "${BLUE}📡 Creating Docker credentials secret '$DOCKER_SECRET_NAME'...${NC}"

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
        echo -e "${GREEN}✅ Docker credentials secret created or updated successfully${NC}"
    elif [[ "$SECRET_STATUS" -eq 409 || "$SECRET_RESPONSE" == *"already exists"* ]]; then
        echo -e "${BLUE}ℹ️ Secret '$DOCKER_SECRET_NAME' already exists${NC}"
    else
        echo -e "${YELLOW}⚠️ Could not create Docker credentials secret (HTTP status: $SECRET_STATUS)${NC}"
        if [ -n "$SECRET_REQUEST_ID" ]; then
            echo "Request ID: $SECRET_REQUEST_ID"
        fi
        echo "Response preview:"
        echo "$SECRET_RESPONSE" | head -10
        echo "You may need to create this secret manually via the Quome Cloud dashboard"
        echo "Debug log: $SECRET_DEBUG_FILE"
    fi
fi

# Check if Anthropic API Key is available
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠️ Anthropic API Key not found in .env file${NC}"
    echo "Skipping Anthropic Key secret creation."
    echo "The existing secret '$ANTHROPIC_SECRET_NAME' will be used if available."
else
    # Create Anthropic Key secret
    echo -e "${BLUE}📡 Creating Anthropic Key secret '$ANTHROPIC_SECRET_NAME'...${NC}"

    # API URL for secrets
    SECRETS_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/secrets"
    echo "Secrets API URL: $SECRETS_API_URL"

    # Save detailed debugging output to a file for inspection if needed
    SECRET_DEBUG_FILE="/tmp/quome_secret_debug_$(date +%s).log"

    # Try to create the secret via API (with SSL option if in test mode)
    SECRET_RESPONSE=$(curl $CURL_SSL_OPTION -L -s -w "\nStatus Code: %{http_code}\n" -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "$ANTHROPIC_SECRET_PAYLOAD" \
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
        echo -e "${GREEN}✅ Anthropic Key secret created or updated successfully${NC}"
    elif [[ "$SECRET_STATUS" -eq 409 || "$SECRET_RESPONSE" == *"already exists"* ]]; then
        echo -e "${BLUE}ℹ️ Secret '$ANTHROPIC_SECRET_NAME' already exists${NC}"
    else
        echo -e "${YELLOW}⚠️ Could not create Anthropic Key secret (HTTP status: $SECRET_STATUS)${NC}"
        if [ -n "$SECRET_REQUEST_ID" ]; then
            echo "Request ID: $SECRET_REQUEST_ID"
        fi
        echo "Response preview:"
        echo "$SECRET_RESPONSE" | head -10
        echo "You may need to create this secret manually via the Quome Cloud dashboard"
        echo "Debug log: $SECRET_DEBUG_FILE"
    fi
fi

echo -e "${BLUE}🔄 Updating $APP_NAME application in Quome Cloud...${NC}"

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
                "secret_vars" : {
                    "ANTHROPIC_API_KEY": "anthropic-key",
                    "DATABASE_URL": "pallcare-db-url"
                },
                "registry_secret": "$DOCKER_SECRET_NAME"
            }
        ]
    }
}
EOF
)

# Debug: Show Cloud payload if debug mode is enabled
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${BLUE}Debug: CLOUD_PAYLOAD:${NC}"
    echo "$CLOUD_PAYLOAD" | jq . 2>/dev/null || echo "$CLOUD_PAYLOAD"
    echo ""
fi

# Make the API request to update the app
echo -e "${BLUE}📡 Sending update request to Quome Cloud...${NC}"

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
    echo -e "${GREEN}✅ Cloud deployment update initiated successfully! (HTTP $HTTP_STATUS)${NC}"
    DEPLOYMENT_SUCCESS=true
else
    echo -e "${YELLOW}⚠️ Request did not succeed. Details:${NC}"

    # Classify the error for better debugging
    if [[ "$CURL_EXIT_CODE" -ne 0 ]]; then
        echo -e "${RED}❌ curl command failed with exit code $CURL_EXIT_CODE${NC}"
        echo "Common exit codes:"
        echo "  6: Could not resolve host"
        echo "  7: Failed to connect"
        echo "  28: Operation timeout"
        echo "See debug log for details: $CURL_DEBUG_FILE"
    elif [[ "$HTTP_STATUS" -eq 401 || "$HTTP_STATUS" -eq 403 ]]; then
        echo -e "${RED}❌ Authentication error (HTTP $HTTP_STATUS). Please check your API key.${NC}"
    elif [[ "$HTTP_STATUS" -eq 404 ]]; then
        echo -e "${RED}❌ Resource not found (HTTP $HTTP_STATUS). Incorrect API URL or App/Org ID.${NC}"
    elif [[ "$HTTP_STATUS" -eq 400 ]]; then
        echo -e "${RED}❌ Bad request (HTTP $HTTP_STATUS). Likely an issue with the payload format.${NC}"
        echo "API Response:"
        echo "$UPDATE_RESPONSE"
    elif [[ "$HTTP_STATUS" -eq 0 ]]; then
        echo -e "${RED}❌ No HTTP status received. Connection problem or timeout.${NC}"
    else
        echo -e "${RED}❌ Unexpected HTTP status: $HTTP_STATUS${NC}"
    fi
fi

# Final deployment status report
if [ "$DEPLOYMENT_SUCCESS" = "true" ]; then
    echo ""
    echo -e "${GREEN}🎉 DEPLOYMENT SUCCESS! 🎉${NC}"
    echo -e "${BLUE}⏱️  The new version should be available in about a minute after SBOM scan completes.${NC}"
    echo -e "${BLUE}🔗 Visit: https://demo.quome.cloud/apps/$CLOUD_APP_ID${NC}"

    # Add verification of deployment status
    echo -e "${BLUE}🔍 Verifying deployment status...${NC}"

    # Wait for a moment to allow deployment to start
    echo -e "${YELLOW}⏳ Waiting 10 seconds for deployment to start...${NC}"
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
            echo -e "${GREEN}✅ Deployment verified! Application is running.${NC}"
            DEPLOYMENT_VERIFIED=true
            break
        elif [[ "$APP_STATUS" == *"\"status\":\"deploying\""* || "$APP_STATUS" == *"\"state\":\"deploying\""* ]]; then
            echo -e "${YELLOW}⏳ Application is still being deployed...${NC}"
        elif [[ "$APP_STATUS" == *"\"status\":\"error\""* || "$APP_STATUS" == *"\"state\":\"error\""* ]]; then
            echo -e "${RED}❌ Deployment failed. Application is in error state.${NC}"
            echo "Error details:"
            echo "$APP_STATUS" | grep -o '"error":"[^"]*"' || echo "No error details available"
            DEPLOYMENT_VERIFIED=false
            break
        else
            echo -e "${YELLOW}🔄 Deployment status is unclear. Current response:${NC}"
            echo "$APP_STATUS" | head -10
        fi

        # If we haven't verified yet, wait and try again
        if [ "$DEPLOYMENT_VERIFIED" != "true" ] && [ $VERIFICATION_ATTEMPTS -lt $MAX_VERIFICATION_ATTEMPTS ]; then
            echo -e "${YELLOW}⏳ Waiting 10 seconds before next check...${NC}"
            sleep 10
        fi
    done

    # Final verification message
    if [ "$DEPLOYMENT_VERIFIED" = "true" ]; then
        echo -e "${GREEN}✅ DEPLOYMENT VERIFICATION SUCCESSFUL!${NC}"
        echo -e "${GREEN}🚀 The application is now running with port configuration:${NC}"
        echo "  - App Port: 5000"
        echo "  - Container Port: 5000"
    else
        if [ $VERIFICATION_ATTEMPTS -ge $MAX_VERIFICATION_ATTEMPTS ]; then
            echo -e "${YELLOW}⚠️ Deployment verification timed out after $(($MAX_VERIFICATION_ATTEMPTS * 10)) seconds.${NC}"
            echo "The deployment might still be in progress."
            echo "Please check the Quome Cloud dashboard manually."
        else
            echo -e "${RED}❌ Deployment verification failed.${NC}"
            echo "Please check the Quome Cloud dashboard for more details."
        fi
    fi
else
    echo ""
    echo -e "${RED}❌ DEPLOYMENT FAILED ❌${NC}"
    echo "Last API Response:"
    echo "$UPDATE_RESPONSE"
    echo ""
    echo -e "${BLUE}Detailed troubleshooting steps:${NC}"
    echo "  1. Check your API key is correct and not expired"
    echo "     Current key starts with: ${API_KEY:0:8}..."
    echo "  2. Verify Organization ID ($CLOUD_ORG_ID) and App ID ($CLOUD_APP_ID) are correct"
    echo "  3. Confirm the Quome Cloud API endpoint ($CLOUD_API_URL) is reachable"
    echo "  4. Ensure the image ($IMAGE_NAME) exists and is properly tagged"
    echo "  5. Examine the debug log: $CURL_DEBUG_FILE"
    echo ""
    echo "You can retry the deployment or contact Quome Cloud support if the issue persists."
    exit 1
fi

# Update the current Intel tag in .env file if it exists
if [ -f "$ENV_FILE" ]; then
    # Check if tag variable already exists in the file
    if grep -q "^INTEL_CURRENT_TAG=" "$ENV_FILE"; then
        # Replace existing tag line - macOS safe version
        sed -i '' "s/^INTEL_CURRENT_TAG=.*/INTEL_CURRENT_TAG=$TAG/" "$ENV_FILE" 2>/dev/null || \
        sed -i "s/^INTEL_CURRENT_TAG=.*/INTEL_CURRENT_TAG=$TAG/" "$ENV_FILE"
        echo -e "${GREEN}📝 Updated INTEL_CURRENT_TAG in .env file to: $TAG${NC}"
    else
        # Add tag to the file
        echo "INTEL_CURRENT_TAG=$TAG" >> "$ENV_FILE"
        echo -e "${GREEN}📝 Added INTEL_CURRENT_TAG=$TAG to .env file${NC}"
    fi
fi

echo ""
echo -e "${BLUE}📌 Deployment Summary:${NC}"
echo "- Application: $APP_NAME"
echo "- Image: $IMAGE_NAME"
echo "- App Port: 5000, Container Port: 5000"
echo "- API URL: $CLOUD_API_URL"
echo "- Deployment Status: $([ "$DEPLOYMENT_SUCCESS" = "true" ] && echo -e "${GREEN}✅ SUCCESS${NC}" || echo -e "${RED}❌ FAILED${NC}")"
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

        # Get deployment logs using our fetch_logs function
        echo "📋 Retrieving deployment logs..."
        fetch_logs

        # The function sets up APP_LOGS and LOG_SIZE globally

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

        # Get deployment logs if available using our fetch_logs function
        echo "📋 Attempting to retrieve any available logs..."
        fetch_logs

        if [ $LOG_SIZE -gt 0 ]; then

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
