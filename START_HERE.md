# SteadywellOS - Getting Started Guide

Welcome to SteadywellOS, a comprehensive palliative care coordination platform. This guide will help you set up and run the application in a few simple steps.

## Prerequisites

Before you begin, ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Just](https://github.com/casey/just#installation) (optional but recommended for easier command execution)

## Quick Setup (Option 1) - One Command Setup

For the quickest setup, run:

```bash
./start.sh
```

This will:
1. Set executable permissions for all scripts
2. Install dependencies and create configuration files
3. Start the application

## Step-by-Step Setup (Option 2)

If you prefer a more deliberate approach, follow these steps:

### Step 1: Set script permissions

```bash
chmod +x setup_permissions.sh
./setup_permissions.sh
```

### Step 2: Install dependencies and configure environment

```bash
# Using Just (if installed)
just install

# Or using the script directly
./scripts/install.sh
```

### Step 3: Start the application

```bash
# Using Just (if installed)
just up

# Or using the script directly
./scripts/up.sh
```

### Step 4: Initialize and seed the database (if needed)

```bash
# Using Just (if installed)
just db-init
just db-seed

# Or using the scripts directly
./scripts/db_init.sh
./scripts/db_seed.sh
```

## Accessing the Application

After successful setup, the application will be available at:

**URL**: [http://localhost:8080](http://localhost:8080)

**Default login credentials**:
- Admin: `admin` / `password123`
- Nurse: `nurse1` / `password123`
- Physician: `physician` / `password123`

⚠️ **Important**: Change these default passwords in a production environment!

## Common Commands

| Task | Just Command | Script Command |
|------|-------------|----------------|
| Start application | `just up` | `./scripts/up.sh` |
| Stop application | `just down` | `./scripts/down.sh` |
| View logs | `just logs` | `docker-compose logs -f` |
| Reset database | `just db-reset` | `./scripts/db_reset.sh` |
| Check status | `just status` | `docker-compose ps` |

## Next Steps

- Explore the application features and workflows
- Review the complete documentation in the `docs/` directory
- Modify environment variables in the `.env` file for custom settings

## Troubleshooting

If you encounter issues:

1. Check if Docker is running
2. Ensure ports 8080 and 5432 are available
3. Review logs with `just logs` or `docker-compose logs -f`
4. Try resetting the database with `just db-reset`