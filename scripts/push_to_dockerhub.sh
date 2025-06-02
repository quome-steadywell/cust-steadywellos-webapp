#!/bin/bash
# docker_publish_private.sh - Build, push a private Docker image to a registry

set -e  # Exit on error

# Default values
DEFAULT_USERNAME="technophobe01"
DEFAULT_REPOSITORY="palliative-care-platform"
DEFAULT_DESCRIPTION="Palliative Care Platform"
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
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Error: .env file not found at $ENV_FILE"
  exit 1
else
    ENV_USERNAME=$(grep '^DOCKER_USERNAME=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$ENV_USERNAME" ]; then
        USERNAME=$ENV_USERNAME
    fi
fi

# Check Docker login
if [ -f "$SCRIPT_DIR/docker_login.sh" ]; then
    echo "🔑 Attempting to log in to Docker Hub using credentials from .env file..."
    if "$SCRIPT_DIR/docker_login.sh"; then
        echo "✅ Logged in as $USERNAME"
    else
        # If login fails, ask for credentials
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
    fi
else
    # If login script doesn't exist, prompt for username
    read -p "Docker Hub username [$DEFAULT_USERNAME]: " CUSTOM_USERNAME
    if [ -n "$CUSTOM_USERNAME" ]; then
        USERNAME=$CUSTOM_USERNAME
    fi
fi

if [ -z "$USERNAME" ]; then
    echo "Username is required"
    exit 1
fi

# Get repository and description
read -p "Repository name [$DEFAULT_REPOSITORY]: " REPOSITORY
REPOSITORY=${REPOSITORY:-$DEFAULT_REPOSITORY}

read -p "Description [$DEFAULT_DESCRIPTION]: " DESCRIPTION
DESCRIPTION=${DESCRIPTION:-$DEFAULT_DESCRIPTION}

# Choose which architectures to build (default to both)
read -p "Which architectures to build? (arm/intel/both) [both]: " BUILD_CHOICE
BUILD_CHOICE=${BUILD_CHOICE:-both}

# Parse architecture choice
case "$BUILD_CHOICE" in
    arm)
        ARCHITECTURES=("arm")
        ;;
    intel)
        ARCHITECTURES=("intel")
        ;;
    both|*)
        ARCHITECTURES=("arm" "intel")
        echo "🔄 Building for both ARM and Intel architectures"
        ;;
esac

# Check if Dockerfile has a non-root user
DOCKERFILE="$(dirname "$SCRIPT_DIR")/Dockerfile"
if [ -f "$DOCKERFILE" ]; then
    if ! grep -q "useradd\|adduser\|USER " "$DOCKERFILE"; then
        echo "⚠️  No non-root user found in Dockerfile (Docker Scout warning)"
        read -p "Do you want to add a non-root user to the Dockerfile? (y/n): " ADD_USER
        if [[ "$ADD_USER" == "y" ]]; then
            # Create a temporary file
            TEMP_FILE=$(mktemp)
            
            # Find the position before CMD or at the end of the file
            LINE_NUM=$(grep -n "CMD\|ENTRYPOINT" "$DOCKERFILE" | head -1 | cut -d: -f1)
            
            if [ -n "$LINE_NUM" ]; then
                # Insert non-root user before CMD/ENTRYPOINT
                head -n $((LINE_NUM-1)) "$DOCKERFILE" > "$TEMP_FILE"
                cat >> "$TEMP_FILE" << 'EOL'

# Create a non-root user and switch to it
RUN addgroup --system appgroup && \
    adduser --system --group appuser && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

EOL
                tail -n +$((LINE_NUM)) "$DOCKERFILE" >> "$TEMP_FILE"
            else
                # Append non-root user at the end
                cp "$DOCKERFILE" "$TEMP_FILE"
                cat >> "$TEMP_FILE" << 'EOL'

# Create a non-root user and switch to it
RUN addgroup --system appgroup && \
    adduser --system --group appuser && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser
EOL
            fi
            
            # Replace the original file
            mv "$TEMP_FILE" "$DOCKERFILE"
            echo "✅ Added non-root user to Dockerfile"
        fi
    else
        echo "✅ Dockerfile already has a non-root user configured"
    fi
else
    echo "⚠️  Dockerfile not found at $(dirname "$SCRIPT_DIR")/Dockerfile"
fi

# Get port for examples
read -p "Port for example commands [${DEFAULT_PORT}]: " PORT
PORT=${PORT:-$DEFAULT_PORT}

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
read -p "Version number (e.g., 0.0.1) [leave empty for auto-increment]: " VERSION_NUMBER
if [ -n "$VERSION_NUMBER" ]; then
    ARM_TAG="arm-$VERSION_NUMBER"
    INTEL_TAG="intel-$VERSION_NUMBER"
    echo "🏷️  Using version $VERSION_NUMBER for all architectures"
fi

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
    
    # Build and push using buildx
    docker buildx build --platform $PLATFORM -t $IMAGE_NAME --push .
    
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
            }' "$ENV_FILE" > "$TMP_ENV_FILE"
            
            # Replace the original file
            mv "$TMP_ENV_FILE" "$ENV_FILE"
        else
            # Add tag to the file
            echo "$TAG_ENV_VAR=$TAG" >> "$ENV_FILE"
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
    docker manifest create "${MANIFEST_ARGS[@]}"
    docker manifest push "$USERNAME/$REPOSITORY:latest"
    
    echo "✅ Multi-architecture 'latest' tag created"
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
    echo "- $USERNAME/$REPOSITORY:$INTEL_TAG (AMD64 architecture)"
fi
if [ ${#ARCHITECTURES[@]} -gt 1 ]; then
    echo "- $USERNAME/$REPOSITORY:latest (Multi-architecture)"
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
        echo "   docker pull $USERNAME/$REPOSITORY:$INTEL_TAG  # For AMD64 machines"
    fi
fi
echo ""
echo "3. Run the container:"
if [ ${#ARCHITECTURES[@]} -gt 1 ]; then
    echo "   docker run -p $PORT:$PORT $USERNAME/$REPOSITORY:latest"
else
    if [[ " ${ARCHITECTURES[*]} " =~ " arm " ]]; then
        echo "   docker run -p $PORT:$PORT $USERNAME/$REPOSITORY:$ARM_TAG"
    fi
    if [[ " ${ARCHITECTURES[*]} " =~ " intel " ]]; then
        echo "   docker run -p $PORT:$PORT $USERNAME/$REPOSITORY:$INTEL_TAG"
    fi
fi
echo ""
echo "4. Or create a docker-compose.yml file:"
cat << EOF
services:
  web:
    image: $USERNAME/$REPOSITORY:${ARCHITECTURES[@]: -1 >= 0 ? ARCHITECTURES[@]: -1 : ARCHITECTURES[0]}
    ports:
      - "$PORT:$PORT"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/palliative_care
    depends_on:
      - db

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=palliative_care

volumes:
  postgres_data:
EOF
