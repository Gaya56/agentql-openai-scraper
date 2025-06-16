#!/usr/bin/env python3
"""Quick dependency check before running full tests."""

import sys
from pathlib import Path

def check_basic_dependencies():
    """Check if basic dependencies are available."""
    print("🔍 Checking basic dependencies...")
    
    missing_deps = []
    
    # Check critical dependencies
    critical_deps = {
        'agentql': 'AgentQL',
        'playwright': 'Playwright', 
        'openai': 'OpenAI',
        'pandas': 'Pandas',
        'loguru': 'Loguru'
    }
    
    for module, name in critical_deps.items():
        try:
            __import__(module)
            print(f"✅ {name} available")
        except ImportError:
            print(f"❌ {name} missing")
            missing_deps.append(name)
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    print("✅ All critical dependencies available")
    return True

if __name__ == "__main__":
    if check_basic_dependencies():
        print("\n🚀 Ready to run full test suite!")
        print("Run: python test_workflow_pipeline.py")
    else:
        print("\n❌ Please install missing dependencies first")
        sys.exit(1)
