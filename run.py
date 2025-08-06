#!/usr/bin/env python3
"""
AI Food Logger - Simple CLI Runner
Handles virtual environment setup and configuration automatically
"""

import os
import sys
import subprocess
import configparser
import yaml
from pathlib import Path

def ensure_venv():
    """Ensure virtual environment exists and is activated"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("🔧 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # Get the python executable from venv
    if os.name == 'nt':  # Windows
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    return str(python_exe), str(pip_exe)

def install_dependencies(pip_exe):
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    subprocess.run([pip_exe, "install", "-r", "requirements.txt"], check=True)

def load_config():
    """Load configuration from config.ini and config.yaml"""
    config = configparser.ConfigParser()
    
    # Check if config.ini exists
    if not Path("config.ini").exists():
        print("❌ config.ini not found!")
        print("📋 Please copy config.ini.example to config.ini and fill in your API keys")
        print("   Get Gemini API key from: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    config.read("config.ini")
    
    # Load YAML config
    yaml_config = {}
    if Path("config.yaml").exists():
        with open("config.yaml", 'r') as f:
            yaml_config = yaml.safe_load(f)
    
    return config, yaml_config

def setup_environment(config):
    """Set up environment variables from config"""
    if 'gemini' in config and 'api_key' in config['gemini']:
        os.environ['GOOGLE_API_KEY'] = config['gemini']['api_key']
    
    if 'google_sheets' in config:
        if 'sheet_id' in config['google_sheets']:
            os.environ['GOOGLE_SHEETS_ID'] = config['google_sheets']['sheet_id']
        if 'service_account_key' in config['google_sheets']:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config['google_sheets']['service_account_key']

def main():
    """Main CLI runner"""
    if len(sys.argv) < 2:
        print("🍎 AI Food Logger")
        print()
        print("Usage:")
        print("  python run.py log \"I ate 150g grilled chicken breast\"")
        print("  python run.py test                                    # Run all tests")
        print("  python run.py test-unit                               # Run unit tests only")
        print("  python run.py test-integration                        # Run integration tests")
        print("  python run.py setup                                   # Setup and install dependencies")
        print()
        print("Examples:")
        print("  python run.py log \"26g Core Power Vanilla protein shake\"")
        print("  python run.py log \"1 cup of milk\"")
        print("  python run.py log \"100g cooked quinoa\"")
        sys.exit(0)
    
    command = sys.argv[1]
    
    # Setup virtual environment and dependencies
    python_exe, pip_exe = ensure_venv()
    
    if command == "setup":
        install_dependencies(pip_exe)
        print("✅ Setup complete!")
        return
    
    # For other commands, ensure dependencies are installed
    try:
        subprocess.run([python_exe, "-c", "import pytest"], 
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("📦 Installing missing dependencies...")
        install_dependencies(pip_exe)
    
    # Load configuration
    config, yaml_config = load_config()
    setup_environment(config)
    
    # Execute commands
    if command == "log":
        if len(sys.argv) < 3:
            print("❌ Please provide food description")
            print("Example: python run.py log \"150g grilled chicken breast\"")
            sys.exit(1)
        
        food_description = sys.argv[2]
        print(f"🍽️  Analyzing: {food_description}")
        
        # Run the food logger
        cmd = [python_exe, "food_logger.py", food_description]
        subprocess.run(cmd)
    
    elif command == "test":
        print("🧪 Running all tests...")
        cmd = [python_exe, "-m", "pytest", "-v"]
        subprocess.run(cmd)
    
    elif command == "test-unit":
        print("🧪 Running unit tests...")
        cmd = [python_exe, "-m", "pytest", "tests/unit/", "-v"]
        subprocess.run(cmd)
    
    elif command == "test-integration":
        print("🧪 Running integration tests...")
        cmd = [python_exe, "-m", "pytest", "tests/integration/", "-v", "-m", "integration"]
        subprocess.run(cmd)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python run.py' for usage help")
        sys.exit(1)

if __name__ == "__main__":
    main()
