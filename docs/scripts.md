# SteadwellOS Scripts Documentation

This document provides an overview of the scripts used in the SteadwellOS Palliative Care Platform. The scripts are organized by functionality.

## Core System Scripts

| Script | Description |
|--------|-------------|
| `up.sh` | Starts the application, builds containers, and initializes the database if needed |
| `down.sh` | Stops the application and creates a database backup if DEV_STATE=TEST |
| `install.sh` | Sets up the environment, checks prerequisites, and configures permissions |
| `docker_init.sh` | Initializes Docker containers and configuration |

## Database Management

| Script | Description |
|--------|-------------|
| `db_init.sh` | Initializes the database schema |
| `db_seed.sh` | Seeds the database with sample data |
| `db_reset.sh` | Resets the database (drops, creates, and seeds) |
| `db_reset_from_backup.sh` | Restores the database from backup |
| `db_backup.sh` | Creates a backup of the database |
| `clean_db.py` | Cleans up database inconsistencies, especially in protocols |

## Data Verification and Testing

| Script | Description |
|--------|-------------|
| `check_assessments_data.py` | Ensures critical assessment records exist after database restore |
| `check_assessments_api.py` | Tests the assessments API endpoints |
| `check_assessments_by_patient.py` | Checks assessments associated with specific patients |
| `check_api.py` | Tests API functionality |
| `check_data.py` | Verifies overall data consistency |
| `check_db.py` | Checks database connection and tables |
| `check_patients.py` | Verifies patient records |
| `check_protocols.py` | Checks protocol definitions |
| `clear_audit_logs.sh` | Clears audit logs for testing purposes |
| `test_api.py` | Tests API endpoints |
| `test_auth.py` | Tests authentication functionality |
| `test_anthropic.py` | Tests Anthropic API integration |

## Protocol Management

| Script | Description |
|--------|-------------|
| `init_protocols.sh` | Initializes the care protocols |
| `protocol_ingest.py` | Imports protocol definitions into the database |
| `protocol_extractor.py` | Extracts protocol data from the database |
| `show_protocols.sh` | Displays protocols stored in the database |

## Data Maintenance

| Script | Description |
|--------|-------------|
| `fix_data.py` | Fixes data inconsistencies |
| `fix_mary_johnson.py` | Fixes specific data related to the Mary Johnson patient record |
| `export_db.py` | Exports database data |
| `verify_fix.py` | Verifies that fixes have been applied correctly |

## Utility Scripts

| Script | Description |
|--------|-------------|
| `upgrade_anthropic.sh` | Upgrades the Anthropic API client library |

## Understanding Data Verification Scripts

The platform includes several scripts for data verification and integrity:

- **check_assessments_data.py** - Ensures that critical assessment records exist, particularly:
  - Mary Johnson's urgent assessment entries
  - Adequate assessment history for all patients
  - Only adds missing data when needed, doesn't duplicate or modify existing records

- **check_assessments_api.py** - Tests the assessments API endpoints by:
  - Verifying serialization of assessment objects
  - Checking relationships between assessments and related objects
  - Testing API endpoint access and permissions

These scripts help maintain a consistent demonstration and testing environment, especially after database operations.

## Usage Examples

### Database Backup and Restore

```bash
# Create a backup
./scripts/db_backup.sh

# Restore from backup
./scripts/db_reset_from_backup.sh
```

### Testing API Endpoints

```bash
# Test assessments API
python scripts/check_assessments_api.py

# Test a specific assessment record
python scripts/check_assessments_api.py 123  # Where 123 is the assessment ID
```

### Data Verification

```bash
# Verify assessment data consistency
python scripts/check_assessments_data.py

# Check patient records
python scripts/check_patients.py
```
