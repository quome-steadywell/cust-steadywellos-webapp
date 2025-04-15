#!/bin/bash
# test_quome_deployment.sh - Test the complete deployment process

set -e  # Exit on error

echo "===== VERIFYING QUOME DEPLOYMENT PROCESS ====="

# 1. Check if DEV_STATE=TEST is set in .env file
echo "1. Checking .env file..."
if [ -f .env ]; then
  DEV_STATE=$(grep '^DEV_STATE=' .env | cut -d '=' -f2)
  if [ "$DEV_STATE" = "TEST" ]; then
    echo "✅ DEV_STATE=TEST found in .env file"
  else
    echo "⚠️ DEV_STATE is not set to TEST in .env file (current: $DEV_STATE)"
    read -p "Would you like to set DEV_STATE=TEST in .env? (y/n): " SET_TEST
    if [ "$SET_TEST" = "y" ]; then
      if grep -q '^DEV_STATE=' .env; then
        # Update existing line
        sed -i '' 's/^DEV_STATE=.*/DEV_STATE=TEST/' .env
      else
        # Add new line
        echo "DEV_STATE=TEST" >> .env
      fi
      echo "✅ DEV_STATE=TEST has been set in .env file"
    fi
  fi
else
  echo "⚠️ .env file not found. Creating one with DEV_STATE=TEST..."
  echo "DEV_STATE=TEST" > .env
  echo "✅ Created .env file with DEV_STATE=TEST"
fi

# 2. Check if the startup logs page exists
echo "2. Checking startup logs page..."
if grep -q 'View Container Startup Logs' app/templates/login.html; then
  echo "✅ Startup logs link found in login.html"
else
  echo "❌ Startup logs link not found in login.html"
  exit 1
fi

# 3. Check entrypoint script
echo "3. Checking for entrypoint.sh script..."
if [ -f "scripts/entrypoint.sh" ]; then
  echo "✅ entrypoint.sh script exists"
  if grep -q "/app/startup_log.txt" scripts/entrypoint.sh; then
    echo "✅ entrypoint.sh logs to /app/startup_log.txt"
  else
    echo "⚠️ entrypoint.sh does not log to /app/startup_log.txt"
  fi
else
  echo "❌ entrypoint.sh script not found"
  exit 1
fi

# 4. Check docker_startup.sh script
echo "4. Checking for docker_startup.sh script..."
if [ -f "scripts/docker_startup.sh" ]; then
  echo "✅ docker_startup.sh script exists"
  if grep -q "/app/startup_log.txt" scripts/docker_startup.sh; then
    echo "✅ docker_startup.sh logs to /app/startup_log.txt"
  else
    echo "⚠️ docker_startup.sh does not log to /app/startup_log.txt"
  fi
else
  echo "❌ docker_startup.sh script not found"
  exit 1
fi

# 5. Check Dockerfile
echo "5. Checking Dockerfile configuration..."
if grep -q "docker_startup.sh" Dockerfile; then
  echo "✅ Dockerfile includes docker_startup.sh"
else
  echo "❌ Dockerfile does not include docker_startup.sh"
  exit 1
fi

if grep -q "DEV_STATE.*TEST" Dockerfile; then
  echo "✅ Dockerfile checks for DEV_STATE=TEST"
else
  echo "❌ Dockerfile does not check for DEV_STATE=TEST"
  exit 1
fi

# 6. Check if startup-logs endpoint exists
echo "6. Checking startup-logs endpoint in routes.py..."
if grep -q "api_startup_logs" app/routes.py; then
  echo "✅ api_startup_logs endpoint found in routes.py"
else
  echo "❌ api_startup_logs endpoint not found in routes.py"
  exit 1
fi

# 7. Check Quome configuration in push_to_quome.sh
echo "7. Checking Quome configuration..."
if grep -q '"DEV_STATE": "TEST"' scripts/push_to_quome.sh; then
  echo "✅ DEV_STATE=TEST is set in push_to_quome.sh"
else
  echo "❌ DEV_STATE=TEST is not set in push_to_quome.sh"
  exit 1
fi

echo "✨ All checks passed! The deployment process should be correctly configured."
echo "To deploy to Quome, run the following commands:"
echo "1. ./scripts/docker_publish_private.sh"
echo "2. ./scripts/push_to_quome.sh"
echo "Then visit https://app-lakeam.org-jo6rx4t5vemnm.demo.quome.cloud/startup-logs to view the logs"
echo "======================="