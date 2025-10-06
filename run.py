#!/usr/bin/env python3
"""
Quick start script for Pundora.
"""

import os
import sys
import subprocess

def check_requirements():
    """Check if requirements are installed."""
    try:
        import fastapi
        import openai
        import elevenlabs
        return True
    except ImportError:
        return False

def install_requirements():
    """Install requirements."""
    print("📦 Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def main():
    """Main function."""
    print("🎭 Pundora - Dad Joke Generator")
    print("=" * 40)
    
    # Check if requirements are installed
    if not check_requirements():
        print("❌ Requirements not found. Installing...")
        install_requirements()
        print("✅ Requirements installed!")
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("⚠️  .env file not found. Creating from template...")
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ .env file created! Please edit it with your API keys.")
        else:
            print("❌ .env.example not found. Please create .env file manually.")
            return
    
    # Start the application
    print("🚀 Starting Pundora...")
    from main import main as start_app
    start_app()

if __name__ == "__main__":
    main()