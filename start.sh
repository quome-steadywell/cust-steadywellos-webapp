#!/bin/bash
# SteadywellOS Quick Start Script

# Set permissions
chmod +x setup_permissions.sh
./setup_permissions.sh

# Run the installation script
./scripts/install.sh

# Run the startup script
./scripts/up.sh

echo "SteadywellOS is now running at http://localhost:8080"