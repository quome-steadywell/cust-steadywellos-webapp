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

# Seed the database with sample data
db-seed:
    @echo "Seeding database with sample data..."
    @./scripts/db_seed.sh

# Reset the database (wipe and reinitialize)
db-reset:
    @echo "Resetting database..."
    @./scripts/db_reset.sh

# View application logs
logs:
    @echo "Viewing application logs..."
    @docker-compose logs -f

# Install dependencies
install:
    @echo "Installing dependencies..."
    @./scripts/install.sh

# Run tests
test:
    @echo "Running tests..."
    @docker-compose exec web python -m pytest

# Show application status
status:
    @echo "Application status:"
    @docker-compose ps