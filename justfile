# SteadywellOS - Palliative Care Platform Just Commands

# Default recipe to run when just is called without arguments
default:
    @just --list

# Setup the environment and start the application
up:
    @echo "Starting SteadywellOS..."
    @./scripts/up.sh

# Stop the application
down:
    @echo "Stopping SteadywellOS..."
    @./scripts/down.sh

# Rebuild and restart the application
restart: down up
    @echo "SteadywellOS has been restarted"

# Initialize the database
db-init:
    @echo "Initializing database..."
    @./scripts/db_init.sh

# Initialize protocols only
protocols-init:
    @echo "Initializing protocols..."
    @./scripts/init_protocols.sh

# Seed the database with sample data
db-seed:
    @echo "Seeding database with sample data..."
    @./scripts/db_seed.sh

# Reset the database (wipe and reinitialize)
db-reset:
    @echo "Resetting database..."
    @./scripts/db_reset.sh

# Reset the database (wipe and reinitialize) without confirmation
db-reset-force:
    @echo "Force resetting database without confirmation..."
    @./scripts/db_reset.sh --force

# Show protocols in the database
protocols:
    @echo "Showing protocols..."
    @./scripts/show_protocols.sh

# View application logs
logs:
    @echo "Viewing application logs..."
    @docker-compose logs -f

# Install dependencies
install:
    @echo "Installing dependencies..."
    @./scripts/install.sh

# Run tests (optionally with specific markers)
test *args="":
    @echo "Running tests..."
    @docker-compose exec web python -m pytest {{args}}

# Simple test to verify the application is running (no dependencies)
check-app:
    @echo "Checking if the application is up and running..."
    @python tests/simple_test.py

# Run HTTP-based tests (no browser dependencies)
test-http:
    @echo "Running HTTP-based tests..."
    @python tests/http_test.py

# Run UI tests without Selenium (more reliable)
test-ui:
    @echo "Running UI tests..."
    @python tests/ui_test.py

# Run all tests in sequence
test-all:
    @echo "Running all tests..."
    @python tests/simple_test.py && \
    python tests/http_test.py && \
    python tests/ui_test.py && \
    docker-compose exec web python tests/date_test.py

# Run tests for date handling
test-dates:
    @echo "Running date handling tests..."
    @docker-compose exec web python tests/date_test.py

# Show application status
status:
    @echo "Application status:"
    @docker-compose ps

# Upgrade Anthropic library
upgrade-anthropic:
    @echo "Upgrading Anthropic library..."
    @./scripts/upgrade_anthropic.sh