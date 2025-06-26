# Development Setup Guide

This guide helps you set up the development environment for the SteadwellOS Palliative Care Platform.

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- uv (Python package manager)

## Initial Setup

After cloning the repository:

### 1. Create and activate virtual environment

```bash
# Install uv if not already installed
pip install uv

# Create virtual environment
uv venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
# Install all project dependencies
uv pip install -r requirements.txt
```

### 3. Initialize development environment

```bash
# This sets up pre-commit hooks for automatic code formatting
./scripts/init_dev_environment.sh
```

### 4. Set up environment variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
```

## Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality:

- **Black**: Automatically formats Python code
- **Trailing whitespace**: Removes trailing spaces
- **End of file fixer**: Ensures files end with a newline
- **YAML/JSON checkers**: Validates configuration files
- **Large file check**: Prevents accidentally committing large files

### Manual formatting

To manually run Black on all files:
```bash
pre-commit run --all-files
```

To bypass hooks in an emergency:
```bash
git commit --no-verify
```

## Development Workflow

1. Always work in feature branches off `develop`
2. Black will automatically format your code on commit
3. Run tests before pushing: `just test-all`
4. Create pull requests to merge into `develop`
