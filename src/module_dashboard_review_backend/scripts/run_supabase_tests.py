#!/usr/bin/env python
"""
Script to run Supabase client tests
This script verifies the test implementation
"""

import subprocess
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

def run_tests():
    """Run the Supabase client tests."""
    print("Running Supabase client tests...")
    print("-" * 50)
    
    # Run pytest with coverage
    cmd = [
        "pytest",
        "tests/test_services/test_supabase_client.py",
        "-v",  # Verbose output
        "--cov=src/services/supabase_client",  # Coverage for Supabase client
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html:coverage_html",  # Generate HTML report
        "-x",  # Stop on first failure
        "--tb=short"  # Short traceback format
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check coverage
        if result.returncode == 0:
            print("\n" + "=" * 50)
            print("✅ All tests passed!")
            print("=" * 50)
            
            # Check if coverage meets minimum requirement
            if "--cov" in cmd:
                # Parse coverage from output
                for line in result.stdout.split('\n'):
                    if "supabase_client.py" in line and "%" in line:
                        coverage_str = line.split()[-1].rstrip('%')
                        try:
                            coverage = float(coverage_str)
                            if coverage >= 90:
                                print(f"✅ Coverage: {coverage}% (meets 90% minimum)")
                            else:
                                print(f"⚠️  Coverage: {coverage}% (below 90% minimum)")
                        except ValueError:
                            pass
        else:
            print("\n" + "=" * 50)
            print("❌ Tests failed!")
            print("=" * 50)
            return 1
            
    except FileNotFoundError:
        print("❌ Error: pytest not found. Please install requirements:")
        print("   pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_tests())
