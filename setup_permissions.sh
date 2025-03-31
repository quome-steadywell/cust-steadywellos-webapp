#!/bin/bash
# Set executable permissions for all scripts in the project

# Make all scripts executable
chmod +x scripts/*.sh
chmod +x scripts/*.py
chmod +x *.sh 2>/dev/null || true

echo "Permissions set. You can now run 'just install' or './scripts/install.sh' to set up the project."