#!/bin/bash
# verify_docker_pull.sh - Verify Docker Hub credentials by pulling an image
#
# This script pulls an image from Docker Hub using credentials from .env
# Useful for verifying whether your Docker Hub token works correctly

set -e  # Exit on error

# Set color codes for prettier output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Get script directory and environment file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"

# Default values
DEFAULT_USERNAME="technophobe01"
DEFAULT_REPOSITORY="palliative-carer-platform"
DEFAULT_TAG="intel-0.0.29"

# Process command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --username|-u) USERNAME="$2"; shift 2 ;;
        --repository|-r) REPOSITORY="$2"; shift 2 ;;
        --tag|-t) TAG="$2"; shift 2 ;;
        --debug|-d) DEBUG_MODE=true; shift ;;
        --help|-h) 
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --username, -u USERNAME   Specify Docker Hub username"
            echo "  --repository, -r REPO     Specify Docker repository name"
            echo "  --tag, -t TAG             Specify Docker image tag"
            echo "  --debug, -d               Enable debug mode"
            echo "  --help, -h                Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
done

# Load environment variables from .env if it exists
if [ -f "$ENV_FILE" ]; then
    echo -e "${BLUE}📋 Loading configuration from .env file...${NC}"

    # Get Docker username
    if [ -z "$USERNAME" ]; then
        ENV_USERNAME=$(grep '^DOCKER_USERNAME=' "$ENV_FILE" | cut -d '=' -f2)
        if [ -n "$ENV_USERNAME" ]; then
            # Strip quotes if present
            USERNAME=$(echo "$ENV_USERNAME" | sed -e 's/^"//' -e 's/"$//')
            echo -e "${GREEN}✅ Using Docker username: $USERNAME from .env file${NC}"
        else
            USERNAME=$DEFAULT_USERNAME
            echo -e "${YELLOW}⚠️ No DOCKER_USERNAME found in .env file, using default: $USERNAME${NC}"
        fi
    fi
    
    # Get Docker token
    DOCKER_TOKEN=$(grep '^DOCKER_TOKEN=' "$ENV_FILE" | cut -d '=' -f2)
    if [ -n "$DOCKER_TOKEN" ]; then
        # Strip quotes if present
        DOCKER_TOKEN=$(echo "$DOCKER_TOKEN" | sed -e 's/^"//' -e 's/"$//')
        echo -e "${GREEN}✅ Found DOCKER_TOKEN in .env file${NC}"
    else
        echo -e "${RED}❌ No DOCKER_TOKEN found in .env file${NC}"
        echo -e "${RED}This script requires a Docker Hub token for authentication${NC}"
        exit 1
    fi
    
    # Get Intel tag from env if tag not specified
    if [ -z "$TAG" ]; then
        INTEL_TAG=$(grep '^INTEL_CURRENT_TAG=' "$ENV_FILE" | cut -d '=' -f2)
        if [ -n "$INTEL_TAG" ]; then
            # Strip quotes if present
            TAG=$(echo "$INTEL_TAG" | sed -e 's/^"//' -e 's/"$//')
            echo -e "${GREEN}✅ Using tag from .env file: $TAG${NC}"
        else
            TAG=$DEFAULT_TAG
            echo -e "${YELLOW}⚠️ No INTEL_CURRENT_TAG found in .env file, using default: $TAG${NC}"
        fi
    fi
else
    echo -e "${RED}❌ ERROR: .env file not found at $ENV_FILE${NC}"
    
    # Use defaults if .env file not found
    USERNAME=${USERNAME:-$DEFAULT_USERNAME}
    REPOSITORY=${REPOSITORY:-$DEFAULT_REPOSITORY}
    TAG=${TAG:-$DEFAULT_TAG}
    
    # Prompt for token
    echo "Please enter your Docker Hub token:"
    read -rs DOCKER_TOKEN
    if [ -z "$DOCKER_TOKEN" ]; then
        echo -e "${RED}❌ Docker Hub token is required${NC}"
        exit 1
    fi
fi

# Set repository if not provided
REPOSITORY=${REPOSITORY:-$DEFAULT_REPOSITORY}
echo -e "${GREEN}✅ Using repository: $REPOSITORY${NC}"

# Final Docker image name
IMAGE_NAME="$USERNAME/$REPOSITORY:$TAG"
echo -e "${BLUE}🚀 Attempting to pull image: $IMAGE_NAME${NC}"

# Create temporary docker config with token
DOCKER_CONFIG_DIR=$(mktemp -d)
DOCKER_CONFIG_FILE="$DOCKER_CONFIG_DIR/config.json"

echo '{
  "auths": {
    "https://index.docker.io/v1/": {
      "auth": "'$(echo -n "$USERNAME:$DOCKER_TOKEN" | base64)'"
    }
  }
}' > "$DOCKER_CONFIG_FILE"

echo -e "${BLUE}📝 Created temporary Docker config with credentials${NC}"

# Detect architecture
ARCH=$(uname -m)
PLATFORM_ARG=""
if [[ ("$ARCH" == "arm64" || "$ARCH" == "aarch64") && "$TAG" == intel-* ]]; then
    echo -e "${YELLOW}⚠️ Detected ARM Mac but trying to pull Intel image.${NC}"
    echo "Adding --platform=linux/amd64 to pull command to enable emulation."
    PLATFORM_ARG="--platform=linux/amd64"
fi

# Pull the image using the temporary config
echo -e "${BLUE}🔍 Pulling image from Docker Hub...${NC}"
if DOCKER_CONFIG="$DOCKER_CONFIG_DIR" docker pull $PLATFORM_ARG "$IMAGE_NAME"; then
    echo -e "${GREEN}✅ Successfully pulled image: $IMAGE_NAME${NC}"
    echo -e "${GREEN}✅ Your Docker Hub credentials are working correctly!${NC}"
    PULL_SUCCESS=true
else
    echo -e "${RED}❌ Failed to pull image: $IMAGE_NAME${NC}"
    echo -e "${RED}❌ Your Docker Hub credentials may be invalid or the image doesn't exist${NC}"
    PULL_SUCCESS=false
fi

# Clean up temporary config
rm -rf "$DOCKER_CONFIG_DIR"
echo -e "${BLUE}🧹 Cleaned up temporary Docker config${NC}"

# Verify the image in local Docker
if [ "$PULL_SUCCESS" = true ]; then
    echo -e "${BLUE}🔍 Verifying image in local Docker...${NC}"
    if docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Image verified in local Docker: $IMAGE_NAME${NC}"
        
        # Additional image info
        echo -e "${BLUE}📋 Image details:${NC}"
        docker image inspect "$IMAGE_NAME" --format "ID: {{.Id}}"
        docker image inspect "$IMAGE_NAME" --format "Created: {{.Created}}"
        docker image inspect "$IMAGE_NAME" --format "Size: {{.Size}} bytes"
        
        # Check if quome-specific settings are present
        echo -e "${BLUE}🔍 Checking for Docker image best practices...${NC}"
        
        # Check for exposed ports
        EXPOSED_PORTS=$(docker image inspect "$IMAGE_NAME" --format '{{range $key, $value := .Config.ExposedPorts}}{{$key}} {{end}}')
        if [ -n "$EXPOSED_PORTS" ]; then
            echo -e "${GREEN}✅ Image exposes ports: $EXPOSED_PORTS${NC}"
        else
            echo -e "${YELLOW}⚠️ Warning: No exposed ports found in the image${NC}"
        fi
        
        # Check for proper CMD/ENTRYPOINT
        CMD=$(docker image inspect "$IMAGE_NAME" --format '{{.Config.Cmd}}')
        ENTRYPOINT=$(docker image inspect "$IMAGE_NAME" --format '{{.Config.Entrypoint}}')
        if [ "$CMD" != "<nil>" ] || [ "$ENTRYPOINT" != "<nil>" ]; then
            echo -e "${GREEN}✅ Image has proper startup command${NC}"
            [ "$ENTRYPOINT" != "<nil>" ] && echo "ENTRYPOINT: $ENTRYPOINT"
            [ "$CMD" != "<nil>" ] && echo "CMD: $CMD"
        else
            echo -e "${YELLOW}⚠️ Warning: No CMD or ENTRYPOINT found in the image${NC}"
        fi
        
        echo -e "${GREEN}🎉 Image verification completed successfully!${NC}"
    else
        echo -e "${RED}❌ Image not found in local Docker despite successful pull${NC}"
    fi
fi

echo -e "${BLUE}📌 Summary:${NC}"
echo "- Docker Hub Account: $USERNAME"
echo "- Repository: $REPOSITORY"
echo "- Tag: $TAG"
echo "- Full Image Name: $IMAGE_NAME"
echo "- Pull Status: $([ "$PULL_SUCCESS" = true ] && echo -e "${GREEN}✅ SUCCESS${NC}" || echo -e "${RED}❌ FAILED${NC}")"

if [ "$PULL_SUCCESS" = false ]; then
    echo -e "${YELLOW}🔍 Troubleshooting suggestions:${NC}"
    echo "1. Check that your Docker Hub token is valid"
    echo "2. Verify that the repository exists and is accessible to your account"
    echo "3. Make sure the tag exists in the repository"
    echo "4. If the repository is private, confirm your account has access permissions"
    echo "5. Try logging in with: docker login -u $USERNAME"
    exit 1
fi

exit 0
