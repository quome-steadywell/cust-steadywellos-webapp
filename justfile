# Palliative Care Platform
set dotenv-load := true

# Default help command
default:
    @just --list

# Command to check if 1Password cli is installed
op_cli_installed := if `command -v op` =~ "" { "true" } else { "false" }

# Wrapper to call scripts with 1Password secret references passed in
# defaults to calling scripts normally if 1Password cli is not installed
_command_wrapper COMMAND:
    #!/usr/bin/env sh
    # Check if .env.secrets exists, if not, just run the command with existing .env
    if [ ! -f .env.secrets ]; then
        {{COMMAND}}
        exit $?
    fi
    
    # If there's already a .env file back it up temporarily
    # that way we don't accidentally clobber the .env file 
    if [ -f .env ]; then
        mv .env .env.tmp
    fi
    
    # Try to inject secrets with 1Password CLI
    injection_success=false
    if {{op_cli_installed}}; then
        # using op inject since this project has plenty of scripts/code that
        # expect a .env file with plaintext secrets
        if op inject -f -i .env.secrets -o .env > /dev/null 2>&1; then
            injection_success=true
        else
            echo "⚠️  1Password injection failed, falling back to original .env file"
        fi
    else
        if cp .env.secrets .env 2>/dev/null; then
            injection_success=true
        else
            echo "⚠️  Failed to copy .env.secrets, falling back to original .env file"
        fi
    fi
    
    # If injection failed, restore the original .env file
    if [ "$injection_success" = "false" ] && [ -f .env.tmp ]; then
        mv .env.tmp .env
    fi
    
    {{COMMAND}}
    
    # Clean up: if we created a backup for the .env file, copy it back, otherwise delete .env
    if [ -f .env.tmp ]; then
        if [ "$injection_success" = "true" ]; then
            mv .env.tmp .env
        fi
    else
        if [ "$injection_success" = "true" ]; then
            rm .env
        fi
    fi

# ========== QUICK START ==========

# Quick development setup (build and start)
dev:
    @echo "⚡ Quick development setup"
    @just build-dev
    @just up-dev

# Quick production test (build and start)
prod:
    @echo "⚡ Quick production test setup"
    @just build-prod
    @just up-prod

# ========== ENVIRONMENTS ==========

# Start development environment (default)
up:
    @echo "🔄 Updating Retell AI webhook for local development..."
    @bash -c "source .venv/bin/activate 2>/dev/null || true && set -a && source .env && set +a && RUNTIME_ENV=local python3 scripts/update_retell_webhook.py" || echo "⚠️  Webhook update skipped (Python/script not available)"
    @echo "🚀 Starting development environment"
    @just _command_wrapper "docker-compose -f docker-compose-dev.yml up -d"
    @echo "✅ Dev environment started at http://localhost:8081"

# Start development environment with logs
up-dev:
    @echo "🔄 Updating Retell AI webhook for local development..."
    @bash -c "source .venv/bin/activate 2>/dev/null || true && set -a && source .env && set +a && RUNTIME_ENV=local python3 scripts/update_retell_webhook.py" || echo "⚠️  Webhook update skipped (Python/script not available)"
    @echo "🚀 Starting development environment"
    @just _command_wrapper "docker-compose -f docker-compose-dev.yml up -d"
    @echo "✅ Dev environment started at http://localhost:8080"
    @echo "📋 View logs: just logs"

# Start production test environment
up-prod:
    @echo "🚀 Starting production test environment"
    @just _command_wrapper "docker-compose -f docker-compose-prod.yml up -d"
    @echo "✅ Prod test environment started at http://localhost:8081"

# Stop all containers
down:
    @echo "🛑 Stopping all containers"
    @just _command_wrapper "docker-compose -f docker-compose-dev.yml down || true"
    @just _command_wrapper "docker-compose -f docker-compose-prod.yml down || true"
    @echo "🛑 Stopping ngrok if running..."
    @pkill -f "ngrok http 8080" || true
    @echo "✅ All containers and ngrok stopped"

# ========== BUILD ==========

# Build development containers
build-dev:
    @echo "🔨 Building development containers"
    @just _command_wrapper "docker-compose -f docker-compose-dev.yml build --no-cache"

# Build production containers
build-prod:
    @echo "🔨 Building production containers"
    @just _command_wrapper "docker-compose -f docker-compose-prod.yml build --no-cache"

# Build both environments
build-all:
    @just build-dev
    @just build-prod

# ========== DATABASE ==========

# Connect to PostgreSQL database
db:
    @echo "🗄️ Connecting to PostgreSQL database"
    @just _command_wrapper "docker-compose -f docker-compose-dev.yml exec db psql -U ${POSTGRES_LOCAL_USER} -d ${POSTGRES_LOCAL_DB}"

# Reset database (development)
db-reset:
    @echo "🗄️ Resetting database"
    @just _command_wrapper "docker-compose -f docker-compose-dev.yml down -v"
    @just _command_wrapper "docker-compose -f docker-compose-dev.yml up -d"
    @echo "✅ Database reset successfully"

# ========== UTILITIES ==========

# View logs
logs:
    @echo "📋 Showing container logs"
    @just _command_wrapper "docker-compose -f docker-compose-dev.yml logs -f"

# Show container status
ps:
    @echo "📊 Container Status"
    @just _command_wrapper "docker-compose -f docker-compose-dev.yml ps"

# Show deployment status
status:
    @echo "📊 Deployment Status"
    @echo "Local: http://localhost:8081"
    @echo "Quome: ${CLOUD_APP_NAME:-Not deployed}"

# Start shell in web container
shell:
    @echo "🐚 Starting shell in web container"
    @just _command_wrapper "docker-compose -f docker-compose-dev.yml exec web bash"

# Clean all Docker resources
clean:
    @echo "🧹 Cleaning all Docker resources"
    @just _command_wrapper "docker-compose -f docker-compose-dev.yml down -v || true"
    @just _command_wrapper "docker-compose -f docker-compose-prod.yml down -v || true"
    @just _command_wrapper "docker system prune -af --volumes"
    @echo "✅ Docker resources cleaned"

# ========== TESTING ==========

# Test API endpoints
test-api:
    @echo "🧪 Testing API endpoints"
    @echo "Health endpoint:"
    curl -s http://localhost:8081/health | jq '.' || curl -s http://localhost:8081/health
    @echo "Status endpoint:"
    curl -s http://localhost:8081/api/status | jq '.' || curl -s http://localhost:8081/api/status

# Test webhook endpoint
test-webhook:
    @echo "🧪 Testing webhook endpoint"
    curl -X POST -H "Content-Type: application/json" \
      -d '{"call_id":"test-call-id","call_status":"completed","to_number":"+1234567890"}' \
      http://localhost:8081/webhook
    @echo "✅ Webhook test completed"

# ========== DEPLOYMENT ==========

# Deploy to Quome Cloud
deploy:
    @echo "🚀 Deploying to Quome Cloud"
    @just _command_wrapper "./scripts/push_to_dockerhub.sh"
    @echo "🔄 Updating Retell AI webhook for production..."
    @python3 scripts/update_retell_webhook.py || echo "⚠️  Webhook update skipped (Python/script not available)"
    @just _command_wrapper "./scripts/push_to_quome.sh"
    @echo "✅ Deployment complete!"

# Check Quome Cloud logs
logs-quome:
    @echo "📋 Fetching Quome Cloud logs"
    curl -H "Authorization: Bearer ${QUOME_KEY}" \
      "https://demo.quome.cloud/api/v1/orgs/${CLOUD_ORG_ID}/apps/${CLOUD_APP_ID}/logs"

# ========== HELP ==========

# Show help information
help:
    @echo "Palliative Care Platform"
    @echo "========================"
    @echo ""
    @echo "🚀 QUICK START:"
    @echo "  just dev     # Build and start development"
    @echo "  just up      # Start development environment"
    @echo "  just logs    # View logs"
    @echo "  just down    # Stop all containers"
    @echo ""
    @echo "🔨 BUILD:"
    @echo "  just build-dev   # Build development containers"
    @echo "  just build-prod  # Build production containers"
    @echo ""
    @echo "🗄️ DATABASE:"
    @echo "  just db          # Connect to database"
    @echo "  just db-reset    # Reset database"
    @echo ""
    @echo "🧪 TESTING:"
    @echo "  just test-api      # Test API endpoints"
    @echo "  just test-webhook  # Test webhook"
    @echo ""
    @echo "🚀 DEPLOYMENT:"
    @echo "  just deploy        # Deploy to Quome Cloud"
    @echo "  just logs-quome    # View Quome logs"