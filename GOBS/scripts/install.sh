#!/bin/bash
# GitHub Organization Backup System - Installation Script

set -e

echo "🚀 Installing GitHub Organization Backup System..."

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: Git is not installed. Please install Git first."
    exit 1
fi

echo "✅ Git is installed: $(git --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install the package in development mode
echo "🔧 Installing package in development mode..."
pip install -e .

# Create configuration files
echo "⚙️  Setting up configuration..."

# Copy example config if it doesn't exist
if [ ! -f config.yaml ]; then
    cp config.example.yaml config.yaml
    echo "📝 Created config.yaml from template"
    echo "   Please edit config.yaml with your organization settings"
else
    echo "📝 config.yaml already exists"
fi

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    cp env.example .env
    echo "📝 Created .env from template"
    echo "   Please edit .env with your credentials"
else
    echo "📝 .env already exists"
fi

# Create backup directory
mkdir -p backups
echo "📁 Created backups directory"

# Make scripts executable
chmod +x backup_organization.py

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit config.yaml with your GitHub organization settings"
echo "2. Edit .env with your API tokens and credentials"
echo "3. Test the connection: python backup_organization.py --list-repos"
echo "4. Run a dry run: python backup_organization.py --dry-run"
echo "5. Start backup: python backup_organization.py"
echo ""
echo "For more information, see README.md" 