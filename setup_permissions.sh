#!/bin/bash
# Set executable permissions for all scripts in the project

# Make the main initialization script executable
chmod +x init.sh

# Make scripts in the scripts directory executable
chmod +x scripts/*.sh
chmod +x scripts/*.py

echo "Permissions set. You can now run ./init.sh to initialize the project."