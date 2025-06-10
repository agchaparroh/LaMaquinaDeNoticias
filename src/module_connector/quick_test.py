#!/usr/bin/env python3
"""
Quick Test Runner - Execute individual tests for debugging
"""

import subprocess
import sys
import os
from pathlib import Path

def run_test(test_name):
    """Run a specific test and show detailed output"""
    
    test_files = {
        "models": "tests/test_models.py",
        "processing": "tests/test_processing.py", 
        "monitor": "tests/test_monitor.py",
        "api": "tests/test_api_client.py",
        "files": "tests/test_file_management.py",
        "integration": "tests/test_integration.py",
        "demo": "demo.py"
    }
    
    if test_name not in test_files:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_files.keys())}")
        return False
    
    test_file = test_files[test_name]
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"🧪 Running {test_name} test...")
    print(f"📁 File: {test_file}")
    print("=" * 50)
    
    try:
        # Run test with live output
        result = subprocess.run([sys.executable, test_file], cwd=Path.cwd())
        
        print("\n" + "=" * 50)
        if result.returncode == 0:
            print(f"✅ {test_name} test PASSED")
        else:
            print(f"❌ {test_name} test FAILED (exit code: {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"💥 Error running test: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python quick_test.py <test_name>")
        print("Available tests: models, processing, monitor, api, files, integration, demo")
        sys.exit(1)
    
    test_name = sys.argv[1].lower()
    success = run_test(test_name)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
