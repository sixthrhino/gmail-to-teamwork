#!/usr/bin/env python3
"""
Quick validation script to verify backend setup.
Run this before deploying to catch configuration issues early.
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Verify Python 3.11+ is installed."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_venv():
    """Check if running in a virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if not in_venv:
        print("⚠️  Not running in a virtual environment")
        print("  Create and activate one with:")
        print("    python3 -m venv venv")
        print("    source venv/bin/activate")
        return False

    print(f"✓ Virtual environment: {sys.prefix}")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    required = ['flask', 'anthropic', 'requests', 'dotenv']
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} not installed")

    if missing:
        print(f"\nInstall missing packages:\n  pip install {' '.join(missing)}")
        return False

    return True


def check_env_file():
    """Check if .env file exists and has required variables."""
    env_file = Path('.env')

    if not env_file.exists():
        print("❌ .env file not found")
        print("  Copy .env.example and fill in your values:\n    cp .env.example .env")
        return False

    print("✓ .env file exists")

    required_vars = [
        'CLAUDE_API_KEY',
        'TEAMWORK_TENANT_URL',
        'TEAMWORK_PROJECT_ID',
        'TEAMWORK_LIST_ID'
    ]

    with open(env_file) as f:
        env_content = f.read()

    missing_vars = [var for var in required_vars if f'{var}=' not in env_content]

    if missing_vars:
        print(f"❌ Missing env variables: {', '.join(missing_vars)}")
        return False

    print("✓ All required env variables found")

    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your-'):
            print(f"  ⚠️  {var} not set or still has placeholder value")

    return True


def check_imports():
    """Verify all modules can be imported."""
    try:
        from modules.claude_parser import ClaudeParser
        print("✓ claude_parser module")
    except Exception as e:
        print(f"❌ claude_parser: {e}")
        return False

    try:
        from modules.teamwork_client import TeamworkClient
        print("✓ teamwork_client module")
    except Exception as e:
        print(f"❌ teamwork_client: {e}")
        return False

    try:
        from modules.validators import validate_task_structure
        print("✓ validators module")
    except Exception as e:
        print(f"❌ validators: {e}")
        return False

    return True


def main():
    """Run all checks."""
    print("Gmail to Teamwork Backend - Setup Verification\n")

    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_venv),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Module Imports", check_imports),
    ]

    results = []
    for check_name, check_fn in checks:
        print(f"\n[{check_name}]")
        try:
            result = check_fn()
            results.append(result)
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    if all(results):
        print("✅ All checks passed! Backend is ready.")
        print("\nRun backend with: python app.py")
        return 0
    else:
        print("❌ Some checks failed. Fix issues above and try again.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
