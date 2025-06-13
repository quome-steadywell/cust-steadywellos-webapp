#!/bin/bash
# push_to_dockerhub.sh - Build and push Docker image to Docker Hub

set -e # Exit on error

# Parse command line options
INTERACTIVE=false
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --interactive|--int)
            INTERACTIVE=true
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
    echo "Palliative Care Platform - Docker Hub Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --interactive, --int   Run in interactive mode (prompts for input)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Default behavior (no options): Non-interactive mode using .env file values"
    echo ""
    echo "Examples:"
    echo "  $0                    # Non-interactive mode (recommended)"
    echo "  $0 --interactive      # Interactive mode with prompts"
    echo "  $0 --int              # Short form of interactive mode"
    exit 0
fi

echo "🚀 Palliative Care Platform - Docker Hub Deployment"
if [ "$INTERACTIVE" = true ]; then
    echo "📝 Mode: INTERACTIVE (will prompt for input)"
else
    echo "🤖 Mode: NON-INTERACTIVE (using .env file values)"
fi
echo ""

set -x

# Default values
DEFAULT_USERNAME="technophobe01"
DEFAULT_REPOSITORY="palliative-care-platform"
DEFAULT_DESCRIPTION="Palliative Care Platform - Production"
DEFAULT_PORT="5000"

# Detect native architecture
NATIVE_ARCH=$(uname -m)
if [[ "$NATIVE_ARCH" == "arm64" || "$NATIVE_ARCH" == "aarch64" ]]; then
	NATIVE_ARCH_PREFIX="arm"
	echo "🖥️  Detected ARM architecture (M-series Mac)"
else
	NATIVE_ARCH_PREFIX="intel"
	echo "🖥️  Detected Intel/AMD architecture"
fi

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
		echo "${arch_prefix}-0.0.1"
	fi
}

# Get script directory and environment file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"
USERNAME=$DEFAULT_USERNAME

# Load environment variables if .env exists
if [ -f "$ENV_FILE" ]; then
	ENV_USERNAME=$(grep '^DOCKER_USERNAME=' "$ENV_FILE" | cut -d '=' -f2)
	if [ -n "$ENV_USERNAME" ]; then
		USERNAME=$ENV_USERNAME
	fi

	# Load DEFAULT_PORT from .env - must exist
	ENV_DEFAULT_PORT=$(grep '^DEFAULT_PORT=' "$ENV_FILE" | cut -d '=' -f2)
	if [ -n "$ENV_DEFAULT_PORT" ]; then
		DEFAULT_PORT=$ENV_DEFAULT_PORT
		echo "📋 Using DEFAULT_PORT from .env: $DEFAULT_PORT"
	else
		echo "❌ ERROR: DEFAULT_PORT not found in .env file"
		echo "Please add DEFAULT_PORT=5000 to your .env file"
		exit 1
	fi
else
	echo "❌ ERROR: .env file not found at $ENV_FILE"
	exit 1
fi

# Check Docker login
if [ -f "$SCRIPT_DIR/docker_login.sh" ]; then
	echo "🔑 Attempting to log in to Docker Hub using credentials from .env file..."
	if "$SCRIPT_DIR/docker_login.sh"; then
		echo "✅ Logged in as $USERNAME"
	else
		# If login fails, handle based on mode
		if [ "$INTERACTIVE" = true ]; then
			echo "🔐 Please log in to Docker Hub manually:"
			docker login

			# Ask for confirmation to continue with the username
			read -p "Continue with username [$USERNAME]? (y/n): " CONTINUE_USERNAME
			if [ "$CONTINUE_USERNAME" != "y" ]; then
				read -p "Docker Hub username: " NEW_USERNAME
				if [ -n "$NEW_USERNAME" ]; then
					USERNAME=$NEW_USERNAME
				fi
			fi
		else
			echo "❌ ERROR: Docker login failed in non-interactive mode"
			echo "Please ensure DOCKER_USERNAME and DOCKER_TOKEN are set in .env file"
			exit 1
		fi
	fi
else
	# If login script doesn't exist
	if [ "$INTERACTIVE" = true ]; then
		read -p "Docker Hub username [$DEFAULT_USERNAME]: " CUSTOM_USERNAME
		if [ -n "$CUSTOM_USERNAME" ]; then
			USERNAME=$CUSTOM_USERNAME
		fi
	else
		echo "❌ ERROR: docker_login.sh script not found and running in non-interactive mode"
		echo "Please ensure docker_login.sh exists or run with --interactive flag"
		exit 1
	fi
fi

if [ -z "$USERNAME" ]; then
	echo "Username is required"
	exit 1
fi

# Get repository and description
if [ "$INTERACTIVE" = true ]; then
    read -p "Repository name [$DEFAULT_REPOSITORY]: " REPOSITORY
    REPOSITORY=${REPOSITORY:-$DEFAULT_REPOSITORY}
    
    read -p "Description [$DEFAULT_DESCRIPTION]: " DESCRIPTION
    DESCRIPTION=${DESCRIPTION:-$DEFAULT_DESCRIPTION}
    
    # Choose which architectures to build (default to both)
    read -p "Which architectures to build? (arm/intel/both) [both]: " BUILD_CHOICE
    BUILD_CHOICE=${BUILD_CHOICE:-both}
else
    # Non-interactive mode: pull from .env file
    ENV_REPOSITORY=$(grep '^DOCKER_REPOSITORY=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -z "$ENV_REPOSITORY" ]; then
        ENV_REPOSITORY=$(grep '^DEFAULT_REPOSITORY=' "$ENV_FILE" | cut -d '=' -f2)
    fi
    ENV_DESCRIPTION=$(grep '^DOCKER_DESCRIPTION=' "$ENV_FILE" | cut -d '=' -f2 | sed 's/^"//;s/"$//')
    if [ -z "$ENV_DESCRIPTION" ]; then
        ENV_DESCRIPTION=$(grep '^DEFAULT_DESCRIPTION=' "$ENV_FILE" | cut -d '=' -f2)
    fi
    ENV_BUILD_CHOICE=$(grep '^DEFAULT_BUILD_CHOICE=' "$ENV_FILE" | cut -d '=' -f2)
    
    REPOSITORY=${ENV_REPOSITORY:-$DEFAULT_REPOSITORY}
    DESCRIPTION=${ENV_DESCRIPTION:-$DEFAULT_DESCRIPTION}
    BUILD_CHOICE=${ENV_BUILD_CHOICE:-both}
    
    echo "📋 Using repository from .env: $REPOSITORY"
    echo "📋 Using description from .env: $DESCRIPTION"
    echo "📋 Using build choice from .env: $BUILD_CHOICE"
fi

# Parse architecture choice
case "$BUILD_CHOICE" in
arm)
	ARCHITECTURES=("arm")
	;;
intel)
	ARCHITECTURES=("intel")
	;;
both | *)
	ARCHITECTURES=("arm" "intel")
	echo "🔄 Building for both ARM and Intel architectures"
	;;
esac

# Note: Dockerfiles already configured with non-root user for security

# Get port for examples
if [ "$INTERACTIVE" = true ]; then
    read -p "Port for example commands [${DEFAULT_PORT}]: " PORT
    PORT=${PORT:-$DEFAULT_PORT}
else
    # Non-interactive mode: use DEFAULT_PORT from .env
    PORT=$DEFAULT_PORT
    echo "📋 Using port from .env: $PORT"
fi

# Make sure buildx is available for multi-architecture builds
docker buildx inspect multiarch-builder >/dev/null 2>&1 || docker buildx create --name multiarch-builder --use
docker buildx use multiarch-builder

# Get the latest tags for each architecture
ARM_TAG=""
INTEL_TAG=""

if [ -f "$ENV_FILE" ]; then
	CURRENT_ARM_TAG=$(grep '^ARM_CURRENT_TAG=' "$ENV_FILE" | cut -d '=' -f2)
	CURRENT_INTEL_TAG=$(grep '^INTEL_CURRENT_TAG=' "$ENV_FILE" | cut -d '=' -f2)

	if [ -n "$CURRENT_ARM_TAG" ]; then
		ARM_TAG=$(increment_tag "$CURRENT_ARM_TAG" "arm")
	else
		ARM_TAG="arm-0.0.1"
	fi

	if [ -n "$CURRENT_INTEL_TAG" ]; then
		INTEL_TAG=$(increment_tag "$CURRENT_INTEL_TAG" "intel")
	else
		INTEL_TAG="intel-0.0.1"
	fi
else
	ARM_TAG="arm-0.0.1"
	INTEL_TAG="intel-0.0.1"
fi

# Option to specify the version
if [ "$INTERACTIVE" = true ]; then
    read -p "Version number (e.g., 0.0.1) [leave empty for auto-increment]: " VERSION_NUMBER
    if [ -n "$VERSION_NUMBER" ]; then
        ARM_TAG="arm-$VERSION_NUMBER"
        INTEL_TAG="intel-$VERSION_NUMBER"
        echo "🏷️  Using version $VERSION_NUMBER for all architectures"
    fi
else
    # Non-interactive mode: use auto-increment (no manual version override)
    echo "🏷️  Using auto-increment version (non-interactive mode)"
fi

# Build the docker image locally first using production configuration
echo "🔨 Building local Docker image with production configuration"
docker-compose -f docker-compose-prod.yml build --no-cache

# Process each architecture
for ARCH in "${ARCHITECTURES[@]}"; do
	if [[ "$ARCH" == "arm" ]]; then
		PLATFORM="linux/arm64"
		TAG="$ARM_TAG"
	else
		PLATFORM="linux/amd64"
		TAG="$INTEL_TAG"
	fi

	# Check if we need to cross-compile
	if [[ "$NATIVE_ARCH_PREFIX" != "$ARCH" ]]; then
		echo "🔄 Cross-compiling for $ARCH architecture ($PLATFORM)"
	else
		echo "🔨 Building for native $ARCH architecture ($PLATFORM)"
	fi

	# Full image name for Docker Hub
	IMAGE_NAME="$USERNAME/$REPOSITORY:$TAG"

	echo "🔨 Building Docker image: $IMAGE_NAME on platform $PLATFORM"

	# Build and push using buildx with build args
	docker buildx build --platform $PLATFORM --provenance false \
		--build-arg IMAGE_VERSION=$TAG \
		--build-arg DEV_STATE=PROD \
		--build-arg FLASK_ENV=production \
		--build-arg DEBUG=false \
		-t $IMAGE_NAME --push .

	echo "✅ Successfully built and pushed $ARCH image: $IMAGE_NAME"

	# Skip Docker Scout for cross-compiled images
	if [[ "$NATIVE_ARCH_PREFIX" == "$ARCH" ]]; then
		echo "📊 Running security scan"
		docker scout quickview $IMAGE_NAME || echo "⚠️  Docker Scout scan failed, but continuing..."
	else
		echo "⏩ Skipping Docker Scout for cross-compiled image (not compatible with different architectures)"
	fi
    
	# Update the tag in .env file
	if [ -f "$ENV_FILE" ]; then
		# Convert architecture to uppercase for env var
		if [[ "$ARCH" == "arm" ]]; then
			TAG_ENV_VAR="ARM_CURRENT_TAG"
		else
			TAG_ENV_VAR="INTEL_CURRENT_TAG"
		fi

		# Check if tag variable already exists in the file
		if grep -q "^$TAG_ENV_VAR=" "$ENV_FILE"; then
			# Create a temporary file for the replacement
			TMP_ENV_FILE=$(mktemp)

			# Use awk for more reliable replacement across platforms
			awk -v var="$TAG_ENV_VAR" -v val="$TAG" '{
                if ($0 ~ "^"var"=") {
                    print var"="val
                } else {
                    print $0
                }
            }' "$ENV_FILE" >"$TMP_ENV_FILE"

			# Replace the original file
			mv "$TMP_ENV_FILE" "$ENV_FILE"
		else
			# Add tag to the file
			echo "$TAG_ENV_VAR=$TAG" >>"$ENV_FILE"
		fi
		echo "📝 Updated $TAG_ENV_VAR in .env file to: $TAG"
	fi
done

# Create a latest tag that is multi-architecture (if both were built)
if [ ${#ARCHITECTURES[@]} -gt 1 ]; then
	echo "🔄 Creating multi-architecture 'latest' tag"

	# Build arguments for the manifest create command
	MANIFEST_ARGS=("$USERNAME/$REPOSITORY:latest")
	for ARCH in "${ARCHITECTURES[@]}"; do
		if [[ "$ARCH" == "arm" ]]; then
			MANIFEST_ARGS+=("$USERNAME/$REPOSITORY:$ARM_TAG")
		else
			MANIFEST_ARGS+=("$USERNAME/$REPOSITORY:$INTEL_TAG")
		fi
	done

	# Create and push the manifest
	docker manifest create --amend "${MANIFEST_ARGS[@]}"
	docker manifest push "$USERNAME/$REPOSITORY:latest"

	echo "✅ Multi-architecture 'latest' tag created"
	
	# Note for Quome Cloud deployment
	echo "📝 Note: For Quome Cloud deployment, use the Intel-specific tag (required for Quome Cloud)"
fi

# Set repository to private and update description
echo "🔒 Setting repository visibility to private"

# Check if the token is available from .env
if [ -f "$ENV_FILE" ]; then
    DOCKER_TOKEN=$(grep '^DOCKER_TOKEN=' "$ENV_FILE" | cut -d '=' -f2)
fi

if [ -n "$DOCKER_TOKEN" ]; then
    # Use token from .env
    echo "Using Docker token from .env file"
    
    # Using token with Docker Hub API
    RESPONSE=$(curl -s -X PATCH \
        -H "Content-Type: application/json" \
        -H "Authorization: JWT $DOCKER_TOKEN" \
        -d "{\"is_private\": true, \"description\": \"$DESCRIPTION\"}" \
        "https://hub.docker.com/v2/repositories/$USERNAME/$REPOSITORY/")
    
    # Check if response contains error
    if [[ "$RESPONSE" == *"error"* ]]; then
        echo "❌ Failed to update repository settings: $RESPONSE"
    else
        echo "✅ Repository set to private and description updated"
    fi
else
    # Prompt for password if token not found
    echo "Enter your Docker Hub password:"
    read -s PASSWORD
    
    # Using username/password with Docker Hub API
    RESPONSE=$(curl -s -X PATCH \
        -H "Content-Type: application/json" \
        -u "$USERNAME:$PASSWORD" \
        -d "{\"is_private\": true, \"description\": \"$DESCRIPTION\"}" \
        "https://hub.docker.com/v2/repositories/$USERNAME/$REPOSITORY/")
    
    # Check if response contains error
    if [[ "$RESPONSE" == *"error"* ]]; then
        echo "❌ Failed to update repository settings: $RESPONSE"
    else
        echo "✅ Repository set to private and description updated"
    fi
fi

# Provide confirmation and examples
echo ""
echo "🎉 Build Complete! Summary:"
echo "📌 Private Image URL: https://hub.docker.com/r/$USERNAME/$REPOSITORY"
echo ""
echo "Available tags:"
if [[ " ${ARCHITECTURES[*]} " =~ " arm " ]]; then
	echo "- $USERNAME/$REPOSITORY:$ARM_TAG (ARM64 architecture)"
fi
if [[ " ${ARCHITECTURES[*]} " =~ " intel " ]]; then
	echo "- $USERNAME/$REPOSITORY:$INTEL_TAG (AMD64 architecture - required for Quome Cloud)"
fi
if [ ${#ARCHITECTURES[@]} -gt 1 ]; then
	echo "- $USERNAME/$REPOSITORY:latest (Multi-architecture)"
	EXAMPLE_TAG="latest"
	echo "📝 Note: Using 'latest' tag which includes Intel architecture (required for Quome Cloud)"
else
	# Use the single architecture tag that was built
	if [[ " ${ARCHITECTURES[*]} " =~ " intel " ]]; then
		EXAMPLE_TAG="$INTEL_TAG"
	else
		EXAMPLE_TAG="$ARM_TAG"
	fi
fi

echo ""
echo "To use this image on another machine:"
echo ""
echo "1. Login to Docker Hub:"
echo "   docker login"
echo ""
echo "2. Pull the appropriate image for your architecture:"
if [ ${#ARCHITECTURES[@]} -gt 1 ]; then
	echo "   docker pull $USERNAME/$REPOSITORY:latest"
	echo "   (This will automatically select the right architecture)"
else
	if [[ " ${ARCHITECTURES[*]} " =~ " arm " ]]; then
		echo "   docker pull $USERNAME/$REPOSITORY:$ARM_TAG  # For ARM64 machines"
	fi
	if [[ " ${ARCHITECTURES[*]} " =~ " intel " ]]; then
		echo "   docker pull $USERNAME/$REPOSITORY:$INTEL_TAG  # For AMD64 machines (Quome Cloud)"
	fi
fi
echo ""
echo "3. Run the container:"
echo "   docker run -p $PORT:$PORT $USERNAME/$REPOSITORY:$EXAMPLE_TAG"
echo ""
echo "4. Or create a docker-compose.yml file:"
cat <<EOF
services:
  web:
    image: $USERNAME/$REPOSITORY:$EXAMPLE_TAG
    ports:
      - "$PORT:$PORT"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/dbname
      - SECRET_KEY=your-secret-key
      - ANTHROPIC_API_KEY=your-api-key
    depends_on:
      - db
  
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: pallcare
      POSTGRES_PASSWORD: pallcarepass
      POSTGRES_DB: pallcare_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF

echo ""
echo "🚀 For Quome Cloud deployment, use the Intel-specific tag: $USERNAME/$REPOSITORY:$INTEL_TAG"
