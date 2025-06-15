#!/usr/bin/env python3
"""Quick setup script for the framework."""

import subprocess
import sys
import os
from pathlib import Path


def main():
    print("🚀 Setting up AgentQL + OpenAI Scraper Framework...\n")
    
    # Create directories
    dirs = ['data', 'logs', 'projects/examples']
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Install requirements
    print("📦 Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Install playwright
    print("\n🎭 Installing Playwright...")
    subprocess.check_call(["playwright", "install", "chromium"])
    
    # Create .env if it doesn't exist
    if not Path(".env").exists():
        print("\n📝 Creating .env file...")
        subprocess.run(["cp", ".env.example", ".env"])
        print("\n⚠️  Please edit .env and add your API keys:")
        print("   - AGENTQL_API_KEY")
        print("   - OPENAI_API_KEY")
    
    print("\n✅ Setup complete!")
    print("\n📖 Next steps:")
    print("1. Add your API keys to .env")
    print("2. Create a new project: python -m core.utils create_project my-scraper")
    print("3. Run your scraper: python -m projects.my-scraper.main")


if __name__ == "__main__":
    main()