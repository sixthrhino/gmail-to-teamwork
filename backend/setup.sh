#!/bin/bash
# Quick setup script for Gmail to Teamwork backend

set -e

echo "📦 Gmail to Teamwork - Backend Setup"
echo "===================================="
echo ""

# Check Python version
echo "🐍 Checking Python..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "📁 Creating virtual environment..."
  python3 -m venv venv
else
  echo "✓ Virtual environment already exists"
fi

# Activate venv
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Run verification
echo ""
echo "✅ Setup complete!"
echo ""
echo "Your virtual environment is activated."
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and add your API keys"
echo "2. Run: python app.py"
echo ""
echo "To run verification: python verify_setup.py"
echo ""
