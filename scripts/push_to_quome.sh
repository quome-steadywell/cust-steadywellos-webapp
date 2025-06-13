#!/bin/bash

# Get script directory and look for deployment_utils.sh there
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/deployment_utils.sh"

setOutputColours

# Parse command line options
RECREATE_SECRETS=false
INTERACTIVE=false
RESEED_DATABASE=false
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --recreate-secrets)
            RECREATE_SECRETS=true
            shift
            ;;
        --interactive|--int)
            INTERACTIVE=true
            shift
            ;;
        --reseed)
            RESEED_DATABASE=true
            shift
            ;;
        -h|--help)
            HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            HELP=true
            break
            ;;
    esac
done

# Show help if requested
if [ "$HELP" = true ]; then
    echo -e "${BLUE}Palliative Care Platform - Deployment Script${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --recreate-secrets    Delete and recreate all Quome Cloud secrets"
    echo "  --interactive, --int  Run in interactive mode (prompts for input)"
    echo "  --reseed             Force database reseed with fresh sample data"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Default behavior (no options): Non-interactive mode using .env file values"
    echo ""
    echo "Examples:"
    echo "  $0                    # Non-interactive mode (recommended)"
    echo "  $0 --interactive      # Interactive mode with prompts"
    echo "  $0 --recreate-secrets # Delete and recreate all secrets"
    echo "  $0 --reseed          # Force reseed database with fresh data"
    echo "  $0 --int --recreate-secrets # Interactive mode with secret recreation"
    exit 0
fi

echo -e "${BLUE}🚀 Palliative Care Platform Deployment${NC}"
if [ "$INTERACTIVE" = true ]; then
    echo -e "${YELLOW}📝 Mode: INTERACTIVE (will prompt for input)${NC}"
else
    echo -e "${GREEN}🤖 Mode: NON-INTERACTIVE (using .env file values)${NC}"
fi
if [ "$RECREATE_SECRETS" = true ]; then
    echo -e "${YELLOW}⚠️  Mode: RECREATE ALL SECRETS (delete and recreate)${NC}"
else
    echo -e "${GREEN}ℹ️  Mode: UPDATE SECRETS (update existing, create new)${NC}"
fi
if [ "$RESEED_DATABASE" = true ]; then
    echo -e "${YELLOW}🌱 Mode: FORCE DATABASE RESEED (overwrite existing data)${NC}"
else
    echo -e "${GREEN}🌱 Mode: PRESERVE EXISTING DATABASE DATA${NC}"
fi
echo ""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# START OF CONFIG
#
# This section is mostly all you should need to configure to be able to deploy an
# app to quome cloud
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Used for smart defaults
DEFAULT_APP_NAME=palliative-care-platform
SCRIPT_DEFAULT_PORT=5000
DEFAULT_DOCKER_DESCRIPTION="Palliative Care Platform - Production"

# Set if you want to deploy using a sqlite db
USE_SQLITE_DB=false

# Will use quome defaults if these are left empty
# SQLITE_ENV_VAR_NAME="SQLITE_DB_PATH"
SQLITE_ENV_VAR_NAME=
SQLITE_MOUNT_PATH="/var/lib/"
SQLITE_DB_SIZE="1Gi"

# Always disable SSL verification
CURL_SSL_OPTION="-k"

# List of all environment variables which will be uploaded to quome cloud as
# secrets - assumption is that they will all be generic secrets
# format is ("ENV_VAR_NAME" ...)
# i.e. ("API_KEY" "DB_URL")
# will create secrets $APPLICATION_NAME-api-key and $APPLICATION_NAME-db-url
declare -a secret_env_vars=("SECRET_KEY" "ANTHROPIC_API_KEY" "RETELL_API_KEY" "POSTGRES_REMOTE_USER" "POSTGRES_REMOTE_PASSWORD" "POSTGRES_REMOTE_HOST")

# List of all environment variables required for the app,
# to provide a default value add =some default value
# i.e. ("DEFAULT_ENV_VAR=default_value" "REQUIRED_ENV_VAR2")
# WARNING: DO NOT PUT ANY SECRETS IN THESE VARS, THEY MAY END UP EXPOSED
# Updated for Flask application deployment to Quome Cloud
declare -a env_vars=("FLASK_APP=run.py" "FLASK_ENV=production" "FLASK_DEBUG=false" "DEBUG=false" "DEV_STATE=PROD" "LOG_LEVEL" "PORT" "SEED_DATABASE" "POSTGRES_REMOTE_DB" "POSTGRES_REMOTE_PORT")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# END OF APP CONFIG
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

echo -e "${BLUE}📋 Loading configuration from .env and environment variables...${NC}"

detectArchitecture

# Check existence for all environment variables and use defaults if provided
processEnvVars env_vars
processEnvVars secret_env_vars

checkForEnvVar "APPLICATION_NAME" "$DEFAULT_APP_NAME"

# Check for DEFAULT_PORT in .env file - it must exist
if [ -f "$ENV_FILE" ]; then
	ENV_DEFAULT_PORT=$(grep '^DEFAULT_PORT=' "$ENV_FILE" | cut -d '=' -f2)
	if [ -z "$ENV_DEFAULT_PORT" ]; then
		echo -e "${RED}❌ ERROR: DEFAULT_PORT not found in .env file${NC}"
		echo -e "${RED}Please add DEFAULT_PORT=5000 to your .env file${NC}"
		exit 1
	fi
else
	echo -e "${RED}❌ ERROR: .env file not found${NC}"
	exit 1
fi

# Quome deployment related env vars - DEFAULT_PORT must come from .env
declare -a quome_deploy_vars=("CLOUD_ORG_ID" "DOCKER_USERNAME" "DOCKER_TOKEN" "DEFAULT_PORT" "DOCKER_REPOSITORY=$APPLICATION_NAME" "DOCKER_DESCRIPTION=$DEFAULT_DOCKER_DESCRIPTION" "DEFAULT_TAG=intel-0.0.1")

# Check for all the required environment variables for quome deployment
processEnvVars quome_deploy_vars
# Find quome key
findQuomeAPIKey

checkForEnvVar "DEFAULT_CONTAINER_PORT" "$DEFAULT_PORT"

# Check for CLOUD_APP_ID - create new app if it's empty
checkForEnvVar "CLOUD_APP_ID" ""
APP_ID_CHECK=$?

# If CLOUD_APP_ID is empty or not found, create a new app
if [ $APP_ID_CHECK -ne 0 ] || [ -z "$CLOUD_APP_ID" ]; then
	echo -e "${YELLOW}⚠️  CLOUD_APP_ID is empty or not found. Creating new app...${NC}"

	# Create the app via direct API call
	echo -e "${BLUE}📦 Creating new app '$APPLICATION_NAME' in Quome Cloud...${NC}"

	# Build the minimal app creation payload
	APP_CREATE_PAYLOAD=$(
		cat <<EOF
{
    "name": "$APPLICATION_NAME"
}
EOF
	)

	# Create the app
	APPS_API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps"
	echo "API URL: $APPS_API_URL"

	CREATE_RESPONSE=$(curl $CURL_SSL_OPTION -L -s -w "\nStatus Code: %{http_code}\n" -X POST \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer $QUOME_API_KEY" \
		-d "$APP_CREATE_PAYLOAD" \
		"$APPS_API_URL")

	# Extract HTTP status
	HTTP_STATUS=$(echo "$CREATE_RESPONSE" | grep "Status Code:" | awk '{print $3}')

	# Check if successful
	if [[ "$HTTP_STATUS" -ge 200 && "$HTTP_STATUS" -lt 300 ]]; then
		# Extract app ID from response
		APP_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

		if [ -n "$APP_ID" ]; then
			echo -e "${GREEN}✅ App created successfully with ID: $APP_ID${NC}"

			# Update the .env file with the new app ID
			if grep -q '^CLOUD_APP_ID=' "$ENV_FILE"; then
				sed -i '' "s/^CLOUD_APP_ID=.*/CLOUD_APP_ID=$APP_ID/" "$ENV_FILE" 2>/dev/null ||
					sed -i "s/^CLOUD_APP_ID=.*/CLOUD_APP_ID=$APP_ID/" "$ENV_FILE"
			else
				echo "CLOUD_APP_ID=$APP_ID" >>"$ENV_FILE"
			fi

			# Reload the environment
			export CLOUD_APP_ID=$APP_ID
			echo -e "${GREEN}📝 Updated CLOUD_APP_ID in .env file${NC}"
		else
			echo -e "${RED}❌ Could not extract app ID from response${NC}"
			echo "Response: $CREATE_RESPONSE"
			exit 1
		fi
	else
		echo -e "${RED}❌ Failed to create app (HTTP status: $HTTP_STATUS)${NC}"
		echo "Response: $CREATE_RESPONSE"
		echo "Organization ID: $CLOUD_ORG_ID"
		echo "API Key (first 5 chars): ${QUOME_API_KEY:0:5}..."
		exit 1
	fi
else
	echo -e "${GREEN}✅ Using existing app ID: $CLOUD_APP_ID${NC}"
fi

# Handle secrets based on user choice
if [ "$RECREATE_SECRETS" = true ]; then
	# Delete and recreate all secrets
	recreateAllSecretsToQuome secret_env_vars "$DOCKER_USERNAME" "$DOCKER_TOKEN"
else
	# Update existing secrets and create new ones (default)
	updateSecretsToQuome secret_env_vars "$DOCKER_USERNAME" "$DOCKER_TOKEN"
fi

echo -e "${BLUE}📦 Updating application configuration...${NC}"

# Get full list of current environment variables
ALL_ENV_VARS=()
for var in "${env_vars[@]}"; do
    if [ -n "${!var}" ]; then
        ALL_ENV_VARS+=("$var")
    fi
done

# Create secret_vars mapping
payload_secret_vars=$(
	{
		for var in "${secret_env_vars[@]}"; do
			lower_name=$(echo $var | sed -e 's/_/-/g' | awk '{print tolower($0)}')
			echo "$var"
			echo "$APPLICATION_NAME-$lower_name"
		done
	} | jq -n -R 'reduce inputs as $i ({}; . + { ($i): (input|(tonumber? // .)) })'
)

payload_env_vars=$(
	{
		# Process regular env_vars
		for var in "${env_vars[@]}"; do
			var_name="$(echo "$var" | cut -d "=" -f1)"
			echo "$var_name"
			# Force specific values for Quome Cloud production deployment
			if [ "$var_name" = "DEV_STATE" ]; then
				echo "PROD"
			elif [ "$var_name" = "FLASK_ENV" ]; then
				echo "production"
			elif [ "$var_name" = "DEBUG" ]; then
				echo "false"
			elif [ "$var_name" = "FLASK_APP" ]; then
				echo "run.py"
			elif [ "$var_name" = "SEED_DATABASE" ]; then
				if [ "$RESEED_DATABASE" = true ]; then
					echo "true"
				else
					echo "${!var_name:-true}"
				fi
			else
				echo "${!var_name:-}"
			fi
		done
		
		# Add FORCE_RESEED separately (controlled by --reseed flag)
		echo "FORCE_RESEED"
		if [ "$RESEED_DATABASE" = true ]; then
			echo "true"
		else
			echo "false"
		fi
	} | jq -n -R 'reduce inputs as $i ({}; . + { ($i): (input // "") })'
)

if [ $USE_SQLITE_DB = true ]; then
	if [ -z $SQLITE_ENV_VAR_NAME ]; then
		sqlite_payload=$(
			cat <<EOF
"sqlite": { "mount_path": "$SQLITE_MOUNT_PATH", "size": "$SQLITE_DB_SIZE" },
EOF
		)
	else
		sqlite_payload=$(
			cat <<EOF
"sqlite": { "mount_path": "$SQLITE_MOUNT_PATH", "env_var":"$SQLITE_ENV_VAR_NAME", "size": "$SQLITE_DB_SIZE" },
EOF
		)
	fi
else
	sqlite_payload=""
fi

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DOCKER IMAGE BUILD AND PUSH
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Get Docker repository name
if [ "$INTERACTIVE" = true ]; then
    read -rp "Repository name [$DOCKER_REPOSITORY]: " CUSTOM_REPOSITORY
    REPOSITORY=${CUSTOM_REPOSITORY:-$DOCKER_REPOSITORY}
else
    # Non-interactive mode: use value from .env or default
    REPOSITORY=$DOCKER_REPOSITORY
    echo -e "${GREEN}📋 Using repository from .env: $REPOSITORY${NC}"
fi

checkForEnvVar "INTEL_CURRENT_TAG" "" >/dev/null
if [ $? -eq 1 ]; then
	echo -e "${YELLOW}ℹ️ No Intel tag found in .env file. Using default: $DEFAULT_TAG${NC}"
else
	echo -e "${GREEN}📋 Found Intel tag in .env file: $INTEL_CURRENT_TAG${NC}"
	DEFAULT_TAG=$INTEL_CURRENT_TAG
fi

if [ "$INTERACTIVE" = true ]; then
    read -rp "Tag to deploy [$DEFAULT_TAG]: " CUSTOM_TAG
    TAG=${CUSTOM_TAG:-$DEFAULT_TAG}
else
    # Non-interactive mode: use default tag
    TAG=$DEFAULT_TAG
    echo -e "${GREEN}📋 Using tag from .env: $TAG${NC}"
fi

# Make sure tag is prefixed with 'intel-' if it's not 'latest'
if [[ "$TAG" != "latest" && ! "$TAG" == intel-* ]]; then
	TAG="intel-$TAG"
	echo -e "${YELLOW}Adding 'intel-' prefix to tag: $TAG${NC}"
fi

# Image to deploy
IMAGE_NAME="$DOCKER_USERNAME/$REPOSITORY:$TAG"
echo -e "${BLUE}🚀 Preparing to deploy image: $IMAGE_NAME${NC}"

# Build the image using production Docker Compose configuration
echo -e "${BLUE}🔨 Building Docker image with production configuration...${NC}"

# Get project directory
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Ensure we're in production mode for the build
export DEV_STATE=PROD
export FLASK_ENV=production
export DEBUG=false

PLATFORM="linux/amd64" # Intel architecture for Quome Cloud
echo "Building for platform: $PLATFORM"

# Make sure buildx is available
docker buildx inspect multiarch-builder >/dev/null 2>&1 || docker buildx create --name multiarch-builder --use
docker buildx use multiarch-builder

# Build using production Dockerfile with production configuration
echo "Building production image: $IMAGE_NAME"

# Build and push directly with buildx using production configuration
docker buildx build \
    --platform $PLATFORM \
    --build-arg IMAGE_VERSION=$TAG \
    --build-arg DEV_STATE=PROD \
    --build-arg FLASK_ENV=production \
    --build-arg DEBUG=false \
    -t $IMAGE_NAME \
    --push \
    -f Dockerfile .

echo -e "${GREEN}✅ Docker build completed successfully${NC}"

# Verify image existence
echo -e "${BLUE}🔍 Verifying image exists on Docker Hub...${NC}"
DOCKER_HUB_API="https://hub.docker.com/v2/repositories/$DOCKER_USERNAME/$REPOSITORY/tags/$TAG"
RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DOCKER_HUB_API")

if [[ "$RESPONSE_CODE" == "200" ]]; then
	echo -e "${GREEN}✅ Successfully verified image exists on Docker Hub: $IMAGE_NAME${NC}"
else
	echo -e "${YELLOW}⚠️ Warning: Could not verify image $IMAGE_NAME on Docker Hub (HTTP $RESPONSE_CODE).${NC}"
	echo "Proceeding with deployment..."
fi

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Push app to quome cloud
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

echo ""
echo -e "${BLUE}📡 Deploying to Quome Cloud...${NC}"

# Always use the port from .env file
CURRENT_PORT=$DEFAULT_PORT

# Create the app payload
if [ -n "$sqlite_payload" ]; then
	app_payload=$(
		cat <<EOF
{
    "name": "$APPLICATION_NAME",
    "spec": {
      "port": $DEFAULT_PORT,
      "containers": [
      {
        "image": "$IMAGE_NAME",
        "name": "app",
        "port": $DEFAULT_PORT,
        "env_vars": $payload_env_vars,
        "secret_vars": $payload_secret_vars,
        $sqlite_payload
        "registry_secret": "$APPLICATION_NAME-docker-credentials"
      }
      ]
    }
}
EOF
	)
else
	app_payload=$(
		cat <<EOF
{
    "name": "$APPLICATION_NAME",
    "spec": {
      "port": $DEFAULT_PORT,
      "containers": [
      {
        "image": "$IMAGE_NAME",
        "name": "app",
        "port": $DEFAULT_PORT,
        "env_vars": $payload_env_vars,
        "secret_vars": $payload_secret_vars,
        "registry_secret": "$APPLICATION_NAME-docker-credentials"
      }
      ]
    }
}
EOF
	)
fi

# Update the app
echo -e "${BLUE}📦 Updating application configuration...${NC}"
echo "NEW CONFIG:"
echo "$app_payload" | jq .

API_URL="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID"
echo "API URL: $API_URL"
echo "Using image: $IMAGE_NAME"

UPDATE_RESPONSE=$(curl $CURL_SSL_OPTION -s -w "\nStatus Code: %{http_code}\n" -X PUT "$API_URL" \
	-H "Authorization: Bearer $QUOME_API_KEY" \
	-H "Content-Type: application/json" \
	-d "$app_payload")

# Extract HTTP status
HTTP_STATUS=$(echo "$UPDATE_RESPONSE" | grep "Status Code:" | awk '{print $3}')

# Display response
echo ""
echo "Response:"
CLEAN_RESPONSE=$(echo "$UPDATE_RESPONSE" | sed '/Status Code:/d')
echo "$CLEAN_RESPONSE" | jq . || echo "$CLEAN_RESPONSE"

# Check if successful
if [[ "$HTTP_STATUS" -ge 200 && "$HTTP_STATUS" -lt 300 ]]; then
	echo -e "${GREEN}✅ Application deployed successfully!${NC}"
	
	# Try to extract domain name
	DOMAIN_NAME=$(echo "$CLEAN_RESPONSE" | jq -r '.domain_name // empty' 2>/dev/null)
	if [ ! -z "$DOMAIN_NAME" ]; then
		echo -e "${BLUE}🌐 Application URL: https://$DOMAIN_NAME${NC}"
	fi
	
	echo -e "${BLUE}📊 Logs URL: https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/apps/$CLOUD_APP_ID/logs${NC}"
else
	echo -e "${RED}❌ Failed to update app (HTTP status: $HTTP_STATUS)${NC}"
fi

echo -e "${GREEN}✅ Deployment complete!${NC}"