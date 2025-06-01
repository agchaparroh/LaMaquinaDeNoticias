# scripts/run_playwright_tests.py
#!/usr/bin/env python3
"""
Simple script to run Playwright tests and verify functionality.
"""

import sys
import os
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_playwright_tests():
    """Run all Playwright tests and report results."""
    print("🎭 Running Playwright Tests...")
    print("=" * 50)
    
    # Load and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests/test_playwright', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}")
    
    if result.errors:
        print("\n⚠️ Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}")
    
    if result.wasSuccessful():
        print("\n✅ All Playwright tests passed!")
        return True
    else:
        print("\n❌ Some tests failed. Check output above.")
        return False

if __name__ == '__main__':
    success = run_playwright_tests()
    sys.exit(0 if success else 1)
