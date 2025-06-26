#!/bin/bash
# Initialize development environment after cloning the repository

echo "🚀 Initializing development environment..."

# Check if we're in a virtual environment
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo "⚠️  Warning: No virtual environment detected."
    echo "💡 Please activate your virtual environment first with: source .venv/bin/activate"
    echo "   Then run this script again."
    exit 1
fi

# Install pre-commit
echo "📦 Installing pre-commit..."
pip install pre-commit

# Install pre-commit hooks
echo "🎣 Installing pre-commit hooks..."
pre-commit install

# Install pre-commit hooks for commit messages (optional)
echo "📝 Installing commit-msg hooks..."
pre-commit install --hook-type commit-msg || true

echo "✅ Development environment initialized!"
echo ""
echo "Pre-commit hooks are now active. Black will automatically format Python files on commit."
echo ""
echo "Useful commands:"
echo "  - Run Black on all files: pre-commit run --all-files"
echo "  - Bypass hooks (emergency): git commit --no-verify"
echo "  - Update hooks: pre-commit autoupdate"
