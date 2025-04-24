# SteadywellOS - Palliative Care Platform Just Commands

# Default recipe to run when just is called without arguments
default:
    @just --list

# Command to check if 1Password cli is installed
op_cli_installed := if `command -v op` =~ "" { "true" } else { "false" }

# Wrapper to call scripts with 1Password secret references passed in
# defaults to calling scripts normally if 1Password cli is not installed
_command_wrapper COMMAND:
    #!/usr/bin/env sh
    # If there's already a .env file back it up temporarily
    # that way we don't accidentally clobber the .env file 
    if [ -f .env ]; then
        mv .env .env.tmp
    fi
    if {{op_cli_installed}}; then
        # using op inject since this project has plenty of scripts/code that
        # expect a .env file with plaintext secrets
        op inject -f -i .env.secrets -o .env > /dev/null
    else
        cp .env.secrets .env
    fi
    {{COMMAND}}
    # if we created a backup for the .env file, copy it back, otherwise delete .env
    if [ -f .env.tmp ]; then
        mv .env.tmp .env
    else
        rm .env
    fi

# Setup the environment and start the application
up:
    @echo "Starting SteadywellOS..."
    @just _command_wrapper "./scripts/up.sh"

# Stop the application
down:
    @echo "Stopping SteadywellOS..."
    @just _command_wrapper "./scripts/down.sh"

# Rebuild and restart the application
restart: down up
    @echo "SteadywellOS has been restarted"

# Initialize the database (delete, initialize, then seed)
db-init:
    @echo "Deleting, initializing, and seeding database..."
    @just _command_wrapper "./scripts/db_reset.sh --force"

# Initialize protocols only
protocols-init:
    @echo "Initializing protocols..."
    @just _command_wrapper "./scripts/init_protocols.sh"

# Seed the database with sample data
db-seed:
    @echo "Seeding database with sample data..."
    @just _command_wrapper "./scripts/db_seed.sh"

# Reset the database (wipe and reinitialize)
db-reset:
    @echo "Resetting database..."
    @just _command_wrapper "./scripts/db_reset.sh"

# Reset the database (wipe and reinitialize) without confirmation
db-reset-force:
    @echo "Force resetting database without confirmation..."
    @just _command_wrapper "./scripts/db_reset.sh --force"

# Reset the database (wipe and restore from backup)
db-reset-from-backup:
    @echo "Resetting database from backup..."
    @just _command_wrapper "./scripts/db_reset_from_backup.sh"

# Reset the database (wipe and restore from backup) without confirmation
db-reset-from-backup-force:
    @echo "Force resetting database from backup without confirmation..."
    @just _command_wrapper "./scripts/db_reset_from_backup.sh --force"

# Backup the database
db-backup:
    @echo "Backing up database..."
    @just _command_wrapper "./scripts/db_backup.sh"

# Show protocols in the database
protocols:
    @echo "Showing protocols..."
    @just _command_wrapper "./scripts/show_protocols.sh"

# View application logs
logs:
    @echo "Viewing application logs..."
    @just _command_wrapper "docker-compose logs -f"

# Install dependencies
install:
    @echo "Installing dependencies..."
    @just _command_wrapper "./scripts/install.sh"

# Run tests (optionally with specific markers)
test *args="":
    @echo "Running tests..."
    @just _command_wrapper "docker-compose exec web python -m pytest {{args}}"

# Simple test to verify the application is running (no dependencies)
check-app:
    @echo "Checking if the application is up and running..."
    @just _command_wrapper "python tests/simple_test.py"

# Run HTTP-based tests (no browser dependencies)
test-http:
    @echo "Running HTTP-based tests..."
    @just _command_wrapper "python tests/http_test.py"

# Run UI tests without Selenium (more reliable)
test-ui:
    @echo "Running UI tests..."
    @just _command_wrapper "python tests/ui_test.py"

# Run all tests in sequence
test-all:
    @echo "Running all tests..."
    @just _command_wrapper "python tests/simple_test.py && \
    python tests/http_test.py && \
    python tests/ui_test.py && \
    python tests/test_autologout.py && \
    docker-compose exec web python tests/date_test.py"

# Run tests for date handling
test-dates:
    @echo "Running date handling tests..."
    @just _command_wrapper "docker-compose exec web python tests/date_test.py"

# Run auto-logout tests
test-autologout:
    @echo "Running auto-logout tests..."
    @just _command_wrapper "python tests/test_autologout.py"

# Show application status
status:
    @echo "Application status:"
    @just _command_wrapper "docker-compose ps"

# Build the Docker container
build:
    @echo "Building Docker container..."
    @just _command_wrapper "docker-compose build"

# Docker command wrappers
ps: (_command_wrapper "docker-compose ps")
list-services: (_command_wrapper "docker-compose config --services")
run SERVICE *COMMAND:
    @just _command_wrapper "docker-compose exec {{SERVICE}} {{COMMAND}}"
terminal SERVICE:
    @just _command_wrapper "docker-compose exec {{SERVICE}} bash"

# Build and push the Docker container to DockerHub
push-to-dockerhub:
    @echo "Building and pushing Docker container to DockerHub..."
    @just _command_wrapper "./scripts/push_to_dockerhub.sh"

# Pull the Docker container and push to Quome
push-to-quome:
    @echo "Pulling Docker container and pushing to Quome..."
    @just _command_wrapper "./scripts/push_to_quome.sh"

# Upgrade Anthropic library
upgrade-anthropic:
    @echo "Upgrading Anthropic library..."
    @just _command_wrapper "./scripts/upgrade_anthropic.sh"
