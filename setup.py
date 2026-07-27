#!/usr/bin/env python3
"""
Setup script for Ednaficator

Handles initial configuration, dependency checking,
and Austrian service setup.
"""

import asyncio
import sys
from pathlib import Path

from ednaficator.config.settings import create_default_config_file, load_config, validate_config


def check_python_version():
    """Check if Python version is 3.11+"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        print(f"   Current version: {sys.version}")
        return False

    print(f"✅ Python {sys.version.split()[0]} detected")
    return True


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "asyncio",
        "requests",
        "pyyaml",
        "pathlib",
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} missing")

    if missing:
        print("\n📦 Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False

    return True


def setup_directories(config: dict):
    """Create necessary directories"""
    directories = [config["memory_path"], "./logs", "./data", "./exports"]

    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True, parents=True)
        print(f"📁 Created directory: {path}")


def setup_austrian_services():
    """Setup Austrian service configurations"""
    print("\n🇦🇹 Austrian Services Setup")
    print("=" * 40)

    print("Optional API keys for enhanced functionality:")
    print("• Wien.gv.at API: https://www.data.gv.at/")
    print("• ÖBB API: https://www.oebb.at/")
    print("• Many services work without API keys!")

    # Create .env file template
    env_template = """# Ednaficator Environment Variables
# Copy this to .env and fill in your values

# Local LLM (Ollama recommended)
EDNA_LLM_ENDPOINT=http://localhost:11434
EDNA_LLM_MODEL=llama3.1:8b

# Austrian Services (Optional)
# WIEN_GOV_API_KEY=your_key_here
# OEBB_API_KEY=your_key_here

# Privacy Settings
EDNA_LOCAL_PROCESSING_ONLY=true
EDNA_ANONYMIZE_LOGS=true

# Debug (set to false for production)
EDNA_DEBUG=true
EDNA_LOG_LEVEL=INFO
"""

    with open(".env.template", "w") as f:
        f.write(env_template)

    print("✅ Created .env.template file")


def test_local_llm():
    """Test local LLM connection"""
    print("\n🤖 Testing Local LLM Connection")
    print("=" * 40)

    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama detected with {len(models)} models")
            for model in models[:3]:  # Show first 3 models
                print(f"   • {model.get('name', 'Unknown')}")
        else:
            print("⚠️  Ollama running but no models detected")
    except Exception:
        print("❌ Ollama not detected")
        print("   Install: https://ollama.ai/")
        print("   Run: ollama pull llama3.1:8b")


async def main():
    """Main setup function"""
    print("🤖 Ednaficator Setup")
    print("=" * 50)
    print("Austrian AI Concierge - Privacy First!")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        return 1

    # Check dependencies
    print("\n📦 Checking Dependencies")
    print("=" * 30)
    if not check_dependencies():
        print("\n💡 Install dependencies with:")
        print("   pip install -r requirements.txt")
        return 1

    # Create config file if it doesn't exist
    config_file = "ednaficator_config.yaml"
    if not Path(config_file).exists():
        print(f"\n⚙️  Creating default config: {config_file}")
        create_default_config_file(config_file)

    # Load and validate config
    config = load_config(config_file)
    if not validate_config(config):
        return 1

    # Setup directories
    print("\n📁 Setting up directories")
    print("=" * 30)
    setup_directories(config)

    # Setup Austrian services
    setup_austrian_services()

    # Test local LLM
    test_local_llm()

    # Final instructions
    print("\n🎯 Setup Complete!")
    print("=" * 20)
    print("\n📋 Next Steps:")
    print("1. Install Ollama: https://ollama.ai/")
    print("2. Pull a model: ollama pull llama3.1:8b")
    print("3. Copy .env.template to .env and configure")
    print("4. Start Edna: python -m ednaficator.main")
    print("\n🇦🇹 Willkommen zu Ednaficator!")

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
