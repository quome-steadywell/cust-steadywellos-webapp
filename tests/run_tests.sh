#!/bin/bash

# Install test dependencies
echo "Installing test dependencies..."
pip install -r tests/requirements.txt

# Run the tests
echo "Running UI tests..."
python -m pytest tests/ui -v

echo "Tests completed."