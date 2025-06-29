#!/bin/bash
# Script to set up pre-commit hooks for Black formatting

echo "Setting up pre-commit hooks for Black formatting..."

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install the pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Run pre-commit on all files to check current state
echo "Running pre-commit on all files to check formatting..."
pre-commit run --all-files || true

echo "Pre-commit hooks installed successfully!"
echo "Black will now automatically format Python files on every commit."
echo ""
echo "To manually run Black on all files, use: pre-commit run --all-files"
echo "To bypass hooks temporarily, use: git commit --no-verify"
