#!/bin/bash
# ACMS Development Environment Setup Script
# Version: 1.0.0
# Date: 2025-11-02
# Owner: Platform.Engineering

set -e  # Exit on error

echo "🚀 Setting up ACMS development environment..."
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [[ $(echo -e "$python_version\n$required_version" | sort -V | head -n1) != "$required_version" ]]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅ pip upgraded"
echo ""

# Install package in editable mode with dev dependencies
echo "📚 Installing ACMS package in editable mode with dev dependencies..."
pip install -e ".[dev]" --quiet
echo "✅ Package installed successfully"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env file created from .env.example"
        echo "⚠️  Please update .env with your configuration"
    else
        echo "⚠️  No .env.example found - skipping .env creation"
    fi
    echo ""
fi

# Run tests to verify setup
echo "🧪 Running tests to verify setup..."
if pytest -v --tb=short -x; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "⚠️  Some tests failed - please review the output above"
fi
echo ""

# Print next steps
echo "======================================"
echo "🎉 Setup complete!"
echo "======================================"
echo ""
echo "📌 Next steps:"
echo "  1. Activate the virtual environment: source .venv/bin/activate"
echo "  2. Update .env with your configuration"
echo "  3. Run tests: pytest -v"
echo "  4. Run linting: black . && ruff check ."
echo "  5. Check types: mypy core/"
echo ""
echo "📖 For more information, see README.md"
echo ""
