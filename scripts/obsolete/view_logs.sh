#!/bin/bash
# view_logs.sh - View logs for a Quome Cloud deployment

set -e  # Exit on error

# Set color codes for prettier output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Required values - will be loaded from .env file
CLOUD_ORG_ID=""
CLOUD_APP_ID=""
DEFAULT_APPLICATION_NAME=""
# URLs will be constructed after loading values from .env
DEBUG_MODE=false

# Get script directory and environment file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"
API_KEY=""
CURL_SSL_OPTION="-k"  # Always disable SSL verification

# Process command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
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

# Load as many values as possible from .env file
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ ERROR: .env file not found at $ENV_FILE${NC}"
    echo -e "${RED}Please create a .env file with the required values:${NC}"
    echo -e "${YELLOW}CLOUD_ORG_ID=your_org_id${NC}"
    echo -e "${YELLOW}CLOUD_APP_ID=your_app_id${NC}"
    exit 1
else
    echo -e "${BLUE}📋 Loading configuration from .env file...${NC}"

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
    
    # Application name (for display purposes)
    ENV_APP_NAME=$(grep '^DEFAULT_APPLICATION_NAME=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$ENV_APP_NAME" ]; then
        # Strip quotes if present
        DEFAULT_APPLICATION_NAME=$(echo "$ENV_APP_NAME" | sed -e 's/^"//' -e 's/"$//')
        echo -e "${GREEN}✅ Using application name from .env file: $DEFAULT_APPLICATION_NAME${NC}"
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
    
    # Check DEV_STATE for testing mode
    DEV_STATE=$(grep '^DEV_STATE=' "$ENV_FILE" | cut -d '=' -f2)
    if [[ "$DEV_STATE" == "TEST" ]]; then
        echo -e "${YELLOW}🧪 Test mode detected in .env (DEV_STATE=TEST)${NC}"
        # Enable debug mode in test environment
        DEBUG_MODE=true
    fi
fi

# Construct API URLs with loaded values
CLOUD_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID"
CLOUD_LOGS_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID/logs"

echo -e "${BLUE}ℹ️ SSL certificate verification disabled (using -k option)${NC}"

# Check for required values
if [ -z "$CLOUD_ORG_ID" ]; then
    echo -e "${RED}❌ Cloud Organization ID is required${NC}"
    read -rp "Enter Cloud Organization ID: " CLOUD_ORG_ID
    if [ -z "$CLOUD_ORG_ID" ]; then
        echo -e "${RED}❌ Cloud Organization ID is required${NC}"
        exit 1
    fi
fi

if [ -z "$CLOUD_APP_ID" ]; then
    echo -e "${RED}❌ Cloud App ID is required${NC}"
    read -rp "Enter Cloud App ID: " CLOUD_APP_ID
    if [ -z "$CLOUD_APP_ID" ]; then
        echo -e "${RED}❌ Cloud App ID is required${NC}"
        exit 1
    fi
fi

# If no API key in .env, prompt for it
if [ -z "$API_KEY" ]; then
    echo "No API key found in .env file. Please enter your Quome Cloud API Key:"
    read -rs API_KEY
    if [ -z "$API_KEY" ]; then
        echo -e "${RED}❌ API Key is required to fetch logs${NC}"
        exit 1
    fi
fi

# Update URLs after prompting for values
CLOUD_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID"
CLOUD_LOGS_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID/logs"

# Determine app name for display
if [ -z "$DEFAULT_APPLICATION_NAME" ]; then
    APP_DISPLAY_NAME="Quome Cloud Application"
else
    APP_DISPLAY_NAME="$DEFAULT_APPLICATION_NAME"
fi

echo -e "${BLUE}📋 Fetching logs for $APP_DISPLAY_NAME...${NC}"

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
            echo "The application is running but no logs are available."
            echo "This could mean:"
            echo "  1. The application hasn't generated any logs yet"
            echo "  2. The logs were recently cleared"
            echo "  3. There's a configuration issue with the logging system"
            
            # Attempt to extract container info
            echo -e "${BLUE}Checking container status...${NC}"
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
            
            echo ""
            echo "Try these troubleshooting steps:"
            echo "  1. Check if the container is correctly configured to output logs"
            echo "  2. Restart the application to generate new logs"
            echo "  3. Verify that your application is writing to stdout/stderr"
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
    else
        echo -e "${RED}Could not retrieve application status${NC}"
        echo "Please check your API key and network connection."
    fi
    
    echo ""
    echo "Check the app dashboard at: https://demo.quome.cloud/apps/$CLOUD_APP_ID"
}

# Function to fetch and display logs
fetch_logs() {
    echo -e "${BLUE}📡 Fetching application logs from Quome Cloud...${NC}"
    
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

# Function to check if application is generating logs
run_log_debug_commands() {
    echo -e "${BLUE}Running debug commands to diagnose log issues...${NC}"
    echo -e "${YELLOW}This will execute commands on your local machine to help diagnose the issue${NC}"
    
    # Create a temporary file for debug info
    DEBUG_LOG_FILE="/tmp/quome_app_debug_$(date +%s).log"
    echo "Debug Log - $(date)" > $DEBUG_LOG_FILE
    
    # 1. Check if Docker is running
    echo -e "${BLUE}1. Checking if Docker is running...${NC}"
    docker --version >> $DEBUG_LOG_FILE 2>&1
    docker ps -a >> $DEBUG_LOG_FILE 2>&1
    
    # 2. Print detailed app info without sensitive data
    echo -e "${BLUE}2. Getting detailed app info...${NC}"
    APP_INFO=$(curl $CURL_SSL_OPTION -L -s -X GET \
        -H "Authorization: Bearer $API_KEY" \
        "$CLOUD_API_URL" 2>/dev/null)
    
    # Sanitize the output to remove sensitive information
    SANITIZED_INFO=$(echo "$APP_INFO" | sed 's/"password":"[^"]*"/"password":"REDACTED"/g' | sed 's/"key":"[^"]*"/"key":"REDACTED"/g')
    echo "$SANITIZED_INFO" >> $DEBUG_LOG_FILE
    
    echo -e "${GREEN}Debug info saved to: $DEBUG_LOG_FILE${NC}"
    echo -e "${YELLOW}You can share this file with technical support for assistance${NC}"
    
    # 3. Suggest immediate actions
    echo -e "${BLUE}Suggested next steps:${NC}"
    echo "1. Try redeploying the application to generate fresh logs"
    echo "2. Ensure your app is configured to output logs to stdout/stderr"
    echo "3. Check the application dashboard for status updates: https://demo.quome.cloud/apps/$CLOUD_APP_ID"
}

# Main logic
if [ "$DIAGNOSE_MODE" = true ]; then
    echo -e "${BLUE}🔍 Running diagnostic tools for Quome Cloud logging issues...${NC}"
    run_log_debug_commands
    exit 0
elif [ "$WATCH_MODE" = true ]; then
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
    # Fetch logs once
    fetch_logs
    
    # If we got no logs or empty logs array, offer to run diagnostics
    if [[ "$APP_LOGS" == "[]" && "$DIAGNOSE_MODE" != true ]]; then
        echo ""
        echo "Would you like to run diagnostic tools to help troubleshoot the logging issue? (y/n)"
        read -r RUN_DIAG
        if [[ "$RUN_DIAG" == "y" || "$RUN_DIAG" == "Y" ]]; then
            run_log_debug_commands
        fi
    fi
fi

# Add a helpful message about the watch option
if [ $? -eq 0 ] && [ "$WATCH_MODE" != true ]; then
    echo ""
    echo "💡 TIP: Available commands:"
    echo "  '$0 --watch'               - Continuously monitor logs"
    echo "  '$0 --watch --interval 30' - Refresh every 30 seconds"
    echo "  '$0 --debug'               - Show detailed debugging information"
    echo "  '$0 --diagnose'            - Run diagnostic tools for log issues"
fi
