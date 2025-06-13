#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"

# Convenient helper for colourful output
setOutputColours() {
	GREEN='\033[0;32m'
	BLUE='\033[0;34m'
	RED='\033[0;31m'
	YELLOW='\033[0;33m'
	NC='\033[0m' # No Color
}

# Function to detect architecture of current machine
detectArchitecture() {
	ARCH=$(uname -m)
	if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
		ARCH_PREFIX="arm"
		HOST_ARCH="arm64"
		echo -e "${BLUE}🖥️ Detected ARM architecture${NC}"
	else
		ARCH_PREFIX="intel"
		HOST_ARCH="amd64"
		echo -e "${BLUE}🖥️ Detected Intel/AMD architecture${NC}"
	fi
}

# Function to parse current tag and increment version
# ARGS
# $1: current tag
# $2: architecture prefix
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

# Checks for existence of an environment variable both in
# the environment and in a .env file.
# If not found and no default is passed, will throw an error.
# ARGS
# $1: var_name - the name of the environment variable
# $2: default value - leave empty if var is required
#
# Returns 0 if key is found or set to default and 1 if key is not found
checkForEnvVar() {
	local var_name=$1
	local default_val=$2

	local env_value="${!var_name}"

	# Check if the environment variable is empty
	if [ -z "$env_value" ]; then
		# Check if it's been set in the env file
		env_value=$(grep "^$var_name=" "$ENV_FILE" | cut -d '=' -f2-)

		# if there's a value in the env file use it
		if [ -n "$env_value" ]; then
			echo -e "${GREEN}✅  Using '$var_name' from .env file${NC}"
			export $var_name="$env_value"
			return 0
		fi

		# if default is empty then it's a required variable
		if [ -z "$default_val" ]; then
			echo -e "${RED}❌  '$var_name' is required ${NC}"
			return 1
		fi
		echo -e "${GREEN}✅  Using default value for '$var_name': $default_val${NC}"
		export $var_name="$default_val"
	else
		echo -e "${GREEN}✅  Using '$var_name' from environment${NC}"
		export $var_name="$env_value"
	fi
	return 0
}

# Processes an array of env vars
# ARGS
# $1: the name of the array to be processed
processEnvVars() {
	local env_vars_to_process=$1[@]
	env_vars_to_process=("${!env_vars_to_process}")

	for i in "${!env_vars_to_process[@]}"; do
		local env_var=${env_vars_to_process[$i]}
		local var_name="$(echo "$env_var" | cut -d "=" -f1)"
		local default_value="$(echo "$env_var" | cut -s -d "=" -f2-)"
		checkForEnvVar "$var_name" "$default_value"
		if [ $? -eq 1 ]; then
			exit 1
		fi
		env_vars_to_process[$i]=$var_name
	done
}

# Finds if there is a provided quome api key
# Accepts QUOME_KEY or QUOME_API_KEY
# Sets QUOME_API_KEY to the found value
findQuomeAPIKey() {
	checkForEnvVar "QUOME_KEY" "" >/dev/null
	if [ $? -eq 1 ]; then
		checkForEnvVar "QUOME_API_KEY" "" >/dev/null
		if [ $? -eq 1 ]; then
			echo -e "${RED}❌  One of ('QUOME_API_KEY', 'QUOME_KEY') is required ${NC}"
		else
			echo -e "${GREEN}✅  Using Quome API Key from var 'QUOME_API_KEY')${NC}"
		fi
	else
		echo -e "${GREEN}✅  Using Quome API Key from var 'QUOME_KEY'${NC}"
		QUOME_API_KEY=$QUOME_KEY
	fi
}

# Updates an environment variable in a .env file
# ARGS
# $1: var_name - the name of the environment variable
# $2; new_value - the value to update .env with
updateVarInEnvFile() {
	local var_name=$1
	local new_value=$2

	echo -e "Writing $var_name to .env file"

	# Write $var_name to .env file
	if grep -q "^$var_name=" "$ENV_FILE"; then
		TMP_ENV_FILE=$(mktemp)

		awk -v var="$var_name" -v val="$new_value" '{
      if ($0 ~ "^"var"=") {
        print var"="val
      } else {
        print $0
      }
  }' "$ENV_FILE" >"$TMP_ENV_FILE"

		mv "$TMP_ENV_FILE" "$ENV_FILE"
	else
		# add $var_name to the file
		echo "$var_name=$new_value" >>"$ENV_FILE"
	fi
	echo "📝 Updated $var_name in .env file"
}

# Pushes a docker credentials secret to Quome cloud if it doesn't already exist
# ARGS
# $1: docker_username - a docker username
# $2: docker_token - a docker PAT
pushDockerSecretToQuome() {
	local docker_username=$1
	local docker_token=$2

	local full_secret_name="$APPLICATION_NAME-docker-credentials"

	echo -e "${BLUE}📡 Creating docker credentials secret '$full_secret_name'...${NC}"

	local secret_payload=$(
		cat <<EOF
{
    "name": "$full_secret_name",
    "type": "docker-credentials",
    "description": "Docker Hub credentials for $docker_username",
    "secret": {
        "auths": {
            "https://index.docker.io/v1/": {
                "username": "$docker_username",
                "password": "$docker_token"
            }
        }
    }
}
EOF
	)

	pushSecretPayloadToQuome "$secret_payload" "$full_secret_name"
}

# Pushes a secret to Quome cloud if it doesn't already exist
# ARGS
# $1: var_name - the environment variable being pushed
# $2: secret_name - what to call the secret in quome cloud
pushGenericSecretToQuome() {
	local var_name=$1
	local secret_name=$2

	local full_secret_name="$APPLICATION_NAME-$secret_name"

	echo -e "${BLUE}📡 Creating secret '$full_secret_name'...${NC}"

	local secret_payload=$(
		cat <<EOF
		{
    	"name": "$full_secret_name",
    	"type": "generic",
    	"description": "$secret_name for $APPLICATION_NAME app",
    	"secret": {
      	"value": "${!var_name}"
    	}
	}
EOF
	)

	pushSecretPayloadToQuome "$secret_payload" "$full_secret_name"
}

# Push a JSON secret to quome
# $1 json_file - path to the json file to be pushed
# $2 secret_name - the name of the secret being pushed
pushJSONSecretToQuome() {
	local json_file=$1
	local secret_name=$2
	local full_secret_name="$APPLICATION_NAME-$secret_name"

	echo -e "${BLUE}📡 Creating JSON secret '$full_secret_name'...${NC}"

	# Read the JSON content and escape it properly
	local json_content=$(cat "$json_file" | jq -c -R . | jq -s -c 'join("")')

	local secret_payload=$(
		cat <<EOF
{
    "name": "$full_secret_name",
    "type": "generic", 
    "description": "$secret_name for $APPLICATION_NAME app",
    "secret": {
        "value": $json_content
    }
}
EOF
	)

	pushSecretPayloadToQuome "$secret_payload" "$full_secret_name"
}

# Push a secret payload to quome cloud
# mostly meant to be a helper for pushGenericSecretToQuome and pushDockerSecretToQuome
# ARGS
# $1 secret_payload - the payload to push
# $2 secret_name - the name of the secret being pushed
pushSecretPayloadToQuome() {
	local secret_payload=$1
	local secret_name=$2

	# Save detailed debugging output to a file for inspection if needed
	local debug_file="/tmp/quome_secret_debug_$(date +%s).log"

	local secrets_api_url="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/secrets"

	local response=$(curl $CURL_SSL_OPTION -L -s -w "\nStatus Code: %{http_code}\n" -X POST \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer $QUOME_API_KEY" \
		-d "$secret_payload" \
		"$secrets_api_url" 2>>"$debug_file")

	local status=$(echo "$response" | grep "Status Code:" | awk '{print $3}')

	# Check if the secret was created successfully
	if [[ "$status" -ge 200 && "$status" -lt 300 ]] ||
		[[ "$response" == *"\"status\":\"success\""* || "$response" == *"\"status\":\"ok\""* ]]; then
		echo -e "${GREEN}✅  Secret '$secret_name' created or updated successfully${NC}"
	elif [[ "$status" -eq 409 || "$response" == *"already exists"* ]]; then
		echo -e "${BLUE}ℹ️  Secret '$secret_name' already exists, deleting and recreating...${NC}"
		
		# First, get the secret ID
		local list_response=$(curl $CURL_SSL_OPTION -L -s \
			-H "Authorization: Bearer $QUOME_API_KEY" \
			"$secrets_api_url" 2>>"$debug_file")
		
		local secret_id=$(echo "$list_response" | jq -r ".secrets[] | select(.name == \"$secret_name\") | .id")
		
		if [ -z "$secret_id" ]; then
			echo -e "${YELLOW}⚠️  Could not find secret ID for '$secret_name', attempting to create anyway...${NC}"
		else
			# Delete the existing secret
			echo -e "${BLUE}🗑️  Deleting existing secret '$secret_name'...${NC}"
			local delete_response=$(curl $CURL_SSL_OPTION -L -s -w "\nStatus Code: %{http_code}\n" -X DELETE \
				-H "Authorization: Bearer $QUOME_API_KEY" \
				"$secrets_api_url/$secret_id" 2>>"$debug_file")
			
			local delete_status=$(echo "$delete_response" | grep "Status Code:" | awk '{print $3}')
			
			if [[ "$delete_status" -eq 204 ]] || [[ "$delete_status" -eq 200 ]]; then
			echo -e "${GREEN}✅ Secret deleted successfully${NC}"
			echo -e "${BLUE}⏳ Waiting for deletion to complete...${NC}"
			sleep 2
			
			# Now recreate the secret
			echo -e "${BLUE}📡 Recreating secret '$secret_name'...${NC}"
			local recreate_response=$(curl $CURL_SSL_OPTION -L -s -w "\nStatus Code: %{http_code}\n" -X POST \
				-H "Content-Type: application/json" \
				-H "Authorization: Bearer $QUOME_API_KEY" \
				-d "$secret_payload" \
				"$secrets_api_url" 2>>"$debug_file")
			
			local recreate_status=$(echo "$recreate_response" | grep "Status Code:" | awk '{print $3}')
			
			if [[ "$recreate_status" -ge 200 && "$recreate_status" -lt 300 ]] ||
				[[ "$recreate_response" == *"\"status\":\"success\""* || "$recreate_response" == *"\"status\":\"ok\""* ]]; then
				echo -e "${GREEN}✅  Secret '$secret_name' recreated successfully${NC}"
			else
				echo -e "${RED}❌  Failed to recreate secret '$secret_name' (HTTP status: $recreate_status)${NC}"
				echo "Recreate response:"
				echo "$recreate_response" | head -10
				echo "Debug log: $debug_file"
			fi
		else
			echo -e "${RED}❌  Failed to delete existing secret '$secret_name' (HTTP status: $delete_status)${NC}"
			echo "Delete response:"
			echo "$delete_response" | head -10
			echo "Debug log: $debug_file"
		fi
		fi
	else
		echo -e "${YELLOW}⚠️  Could not create secret '$secret_name' (HTTP status: $status)${NC}"
		echo "Response preview:"
		echo "$response" | head -10
		echo "You may need to create this secret manually via the Quome Cloud dashboard"
		echo "Debug log: $debug_file"
	fi
}

# Update or create a secret without deleting existing ones
# ARGS
# $1 secret_payload - the payload to push
# $2 secret_name - the name of the secret being pushed
updateSecretToQuome() {
	local secret_payload=$1
	local secret_name=$2

	# Save detailed debugging output to a file for inspection if needed
	local debug_file="/tmp/quome_secret_update_$(date +%s).log"

	local secrets_api_url="https://demo.quome.cloud/api/v1/orgs/$CLOUD_ORG_ID/secrets"

	# First, check if the secret exists
	local list_response=$(curl $CURL_SSL_OPTION -L -s \
		-H "Authorization: Bearer $QUOME_API_KEY" \
		"$secrets_api_url" 2>>"$debug_file")
	
	local secret_id=$(echo "$list_response" | jq -r ".secrets[] | select(.name == \"$secret_name\") | .id")
	
	if [ -n "$secret_id" ]; then
		# Secret exists, update it using PUT
		echo -e "${BLUE}🔄 Updating existing secret '$secret_name'...${NC}"
		local update_response=$(curl $CURL_SSL_OPTION -L -s -w "\nStatus Code: %{http_code}\n" -X PUT \
			-H "Content-Type: application/json" \
			-H "Authorization: Bearer $QUOME_API_KEY" \
			-d "$secret_payload" \
			"$secrets_api_url/$secret_id" 2>>"$debug_file")
		
		local update_status=$(echo "$update_response" | grep "Status Code:" | awk '{print $3}')
		
		if [[ "$update_status" -ge 200 && "$update_status" -lt 300 ]] ||
			[[ "$update_response" == *"\"status\":\"success\""* || "$update_response" == *"\"status\":\"ok\""* ]]; then
			echo -e "${GREEN}✅  Secret '$secret_name' updated successfully${NC}"
		else
			echo -e "${RED}❌  Failed to update secret '$secret_name' (HTTP status: $update_status)${NC}"
			echo "Update response:"
			echo "$update_response" | head -10
			echo "Debug log: $debug_file"
		fi
	else
		# Secret doesn't exist, create it
		echo -e "${BLUE}📡 Creating new secret '$secret_name'...${NC}"
		local create_response=$(curl $CURL_SSL_OPTION -L -s -w "\nStatus Code: %{http_code}\n" -X POST \
			-H "Content-Type: application/json" \
			-H "Authorization: Bearer $QUOME_API_KEY" \
			-d "$secret_payload" \
			"$secrets_api_url" 2>>"$debug_file")
		
		local create_status=$(echo "$create_response" | grep "Status Code:" | awk '{print $3}')
		
		if [[ "$create_status" -ge 200 && "$create_status" -lt 300 ]] ||
			[[ "$create_response" == *"\"status\":\"success\""* || "$create_response" == *"\"status\":\"ok\""* ]]; then
			echo -e "${GREEN}✅  Secret '$secret_name' created successfully${NC}"
		else
			echo -e "${RED}❌  Failed to create secret '$secret_name' (HTTP status: $create_status)${NC}"
			echo "Create response:"
			echo "$create_response" | head -10
			echo "Debug log: $debug_file"
		fi
	fi
}

# Update or create docker credentials secret without deleting
# ARGS
# $1: docker_username - a docker username
# $2: docker_token - a docker PAT
updateDockerSecretToQuome() {
	local docker_username=$1
	local docker_token=$2

	local full_secret_name="$APPLICATION_NAME-docker-credentials"

	echo -e "${BLUE}📡 Updating docker credentials secret '$full_secret_name'...${NC}"

	local secret_payload=$(
		cat <<EOF
{
    "name": "$full_secret_name",
    "type": "docker-credentials",
    "description": "Docker Hub credentials for $docker_username",
    "secret": {
        "auths": {
            "https://index.docker.io/v1/": {
                "username": "$docker_username",
                "password": "$docker_token"
            }
        }
    }
}
EOF
	)

	updateSecretToQuome "$secret_payload" "$full_secret_name"
}

# Update or create a generic secret without deleting
# ARGS
# $1: var_name - the environment variable being pushed
# $2: secret_name - what to call the secret in quome cloud
updateGenericSecretToQuome() {
	local var_name=$1
	local secret_name=$2

	local full_secret_name="$APPLICATION_NAME-$secret_name"

	echo -e "${BLUE}📡 Updating secret '$full_secret_name'...${NC}"

	local secret_payload=$(
		cat <<EOF
		{
    	"name": "$full_secret_name",
    	"type": "generic",
    	"description": "$secret_name for $APPLICATION_NAME app",
    	"secret": {
      	"value": "${!var_name}"
    	}
	}
EOF
	)

	updateSecretToQuome "$secret_payload" "$full_secret_name"
}

# Delete and recreate all secrets for the application
# ARGS
# $1: secret_env_vars_array_name - name of the array containing secret environment variables
# $2: docker_username
# $3: docker_token
recreateAllSecretsToQuome() {
	local secret_env_vars_array_name=$1[@]
	local secret_env_vars_array=("${!secret_env_vars_array_name}")
	local docker_username=$2
	local docker_token=$3

	echo -e "${YELLOW}🗑️  Recreating ALL secrets for application '$APPLICATION_NAME'...${NC}"
	echo -e "${YELLOW}⚠️  This will delete and recreate all existing secrets${NC}"

	# Recreate docker credentials using original method (delete and recreate)
	pushDockerSecretToQuome "$docker_username" "$docker_token"

	# Recreate all other secrets using original method (delete and recreate)
	for var in "${secret_env_vars_array[@]}"; do
		lower_name=$(echo $var | sed -e 's/_/-/g' | awk '{print tolower($0)}')
		pushGenericSecretToQuome $var $lower_name
	done

	echo -e "${GREEN}✅ All secrets recreated successfully${NC}"
}

# Update existing secrets and create new ones (default behavior)
# ARGS
# $1: secret_env_vars_array_name - name of the array containing secret environment variables
# $2: docker_username
# $3: docker_token
updateSecretsToQuome() {
	local secret_env_vars_array_name=$1[@]
	local secret_env_vars_array=("${!secret_env_vars_array_name}")
	local docker_username=$2
	local docker_token=$3

	echo -e "${BLUE}🔄 Updating secrets for application '$APPLICATION_NAME'...${NC}"
	echo -e "${BLUE}ℹ️  This will update existing secrets and create new ones${NC}"

	# Update docker credentials using new method (update or create)
	updateDockerSecretToQuome "$docker_username" "$docker_token"

	# Update all other secrets using new method (update or create)
	for var in "${secret_env_vars_array[@]}"; do
		lower_name=$(echo $var | sed -e 's/_/-/g' | awk '{print tolower($0)}')
		updateGenericSecretToQuome $var $lower_name
	done

	echo -e "${GREEN}✅ All secrets updated successfully${NC}"
}