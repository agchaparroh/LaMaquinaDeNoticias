#!/usr/bin/env python3
"""
Master Test Runner for Module Connector

Executes all test suites and provides comprehensive results
"""

import asyncio
import subprocess
import sys
import os
import time
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")

def print_test_result(test_name, success, duration, details=""):
    status_icon = "✅" if success else "❌"
    status_color = Colors.GREEN if success else Colors.RED
    status_text = "PASSED" if success else "FAILED"
    
    print(f"{status_icon} {Colors.BOLD}{test_name:<35}{Colors.END} "
          f"{status_color}{status_text:<7}{Colors.END} "
          f"{Colors.YELLOW}({duration:.2f}s){Colors.END}")
    
    if details:
        print(f"   {Colors.WHITE}{details}{Colors.END}")

def run_python_test(test_file):
    """Run a Python test file and return success status, duration, and output"""
    start_time = time.time()
    
    try:
        # Add the tests directory to Python path
        test_dir = Path(__file__).parent
        src_dir = test_dir.parent / "src"
        
        # Run the test
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, cwd=test_dir, timeout=30)
        
        duration = time.time() - start_time
        success = result.returncode == 0
        
        # Get last few lines of output for details
        output_lines = result.stdout.split('\n') if result.stdout else []
        if result.stderr:
            output_lines.extend(result.stderr.split('\n'))
        
        details = '\n'.join([line.strip() for line in output_lines[-3:] if line.strip()])
        
        return success, duration, details
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return False, duration, "Test timeout (>30s)"
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Execution error: {str(e)}"

def run_bash_test(script_file):
    """Run a bash script test"""
    start_time = time.time()
    
    try:
        result = subprocess.run([
            "bash", script_file
        ], capture_output=True, text=True, timeout=120)
        
        duration = time.time() - start_time
        success = result.returncode == 0
        
        # Get summary from output
        output_lines = result.stdout.split('\n') if result.stdout else []
        details = '\n'.join([line.strip() for line in output_lines[-2:] if line.strip()])
        
        return success, duration, details
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return False, duration, "Test timeout (>120s)"
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Execution error: {str(e)}"

async def main():
    """Main test runner function"""
    
    print_header("MODULE CONNECTOR TEST SUITE")
    print(f"{Colors.BLUE}Running comprehensive test suite...{Colors.END}\n")
    
    # Test configuration
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    
    # Ensure we're in the right directory
    os.chdir(project_root)
    
    # Test results tracking
    results = []
    total_tests = 0
    passed_tests = 0
    total_duration = 0
    
    # 1. Unit Tests
    print_header("UNIT TESTS")
    
    unit_tests = [
        ("Models Validation", "tests/test_models.py"),
        ("File Processing", "tests/test_processing.py"),
        ("Directory Monitoring", "tests/test_monitor.py"),
        ("API Client", "tests/test_api_client.py"),
        ("File Management", "tests/test_file_management.py"),
    ]
    
    for test_name, test_file in unit_tests:
        if os.path.exists(test_file):
            success, duration, details = run_python_test(test_file)
            print_test_result(test_name, success, duration, details)
            
            results.append((test_name, success, duration))
            total_tests += 1
            if success:
                passed_tests += 1
            total_duration += duration
        else:
            print_test_result(test_name, False, 0, f"File not found: {test_file}")
            results.append((test_name, False, 0))
            total_tests += 1
    
    # 2. Integration Tests
    print_header("INTEGRATION TESTS")
    
    integration_tests = [
        ("Full Integration", "tests/test_integration.py"),
    ]
    
    for test_name, test_file in integration_tests:
        if os.path.exists(test_file):
            success, duration, details = run_python_test(test_file)
            print_test_result(test_name, success, duration, details)
            
            results.append((test_name, success, duration))
            total_tests += 1
            if success:
                passed_tests += 1
            total_duration += duration
        else:
            print_test_result(test_name, False, 0, f"File not found: {test_file}")
            results.append((test_name, False, 0))
            total_tests += 1
    
    # 3. Demo Test
    print_header("DEMO & FUNCTIONAL TESTS")
    
    demo_tests = [
        ("Component Demo", "demo.py"),
    ]
    
    for test_name, test_file in demo_tests:
        if os.path.exists(test_file):
            success, duration, details = run_python_test(test_file)
            print_test_result(test_name, success, duration, details)
            
            results.append((test_name, success, duration))
            total_tests += 1
            if success:
                passed_tests += 1
            total_duration += duration
        else:
            print_test_result(test_name, False, 0, f"File not found: {test_file}")
            results.append((test_name, False, 0))
            total_tests += 1
    
    # 4. Docker Tests (if available)
    print_header("DOCKER TESTS")
    
    if os.path.exists("test_docker.sh"):
        print(f"{Colors.YELLOW}Note: Docker tests require Docker to be running{Colors.END}")
        
        # Check if Docker is available
        try:
            docker_check = subprocess.run(["docker", "--version"], 
                                        capture_output=True, timeout=5)
            docker_available = docker_check.returncode == 0
        except:
            docker_available = False
        
        if docker_available:
            success, duration, details = run_bash_test("test_docker.sh")
            print_test_result("Docker Build & Run", success, duration, details)
            
            results.append(("Docker Tests", success, duration))
            total_tests += 1
            if success:
                passed_tests += 1
            total_duration += duration
        else:
            print_test_result("Docker Build & Run", False, 0, "Docker not available")
            results.append(("Docker Tests", False, 0))
            total_tests += 1
    else:
        print_test_result("Docker Build & Run", False, 0, "test_docker.sh not found")
        results.append(("Docker Tests", False, 0))
        total_tests += 1
    
    # Final Results Summary
    print_header("TEST RESULTS SUMMARY")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"{Colors.BOLD}📊 Overall Results:{Colors.END}")
    print(f"   Tests Passed: {Colors.GREEN}{passed_tests}{Colors.END}")
    print(f"   Tests Failed: {Colors.RED}{total_tests - passed_tests}{Colors.END}")
    print(f"   Success Rate: {Colors.YELLOW}{success_rate:.1f}%{Colors.END}")
    print(f"   Total Duration: {Colors.CYAN}{total_duration:.2f}s{Colors.END}")
    
    print(f"\n{Colors.BOLD}📋 Detailed Results:{Colors.END}")
    for test_name, success, duration in results:
        status_icon = "✅" if success else "❌"
        print(f"   {status_icon} {test_name}: {duration:.2f}s")
    
    # Recommendations
    print_header("RECOMMENDATIONS")
    
    if success_rate >= 90:
        print(f"{Colors.GREEN}🎉 Excellent! Test suite is in great shape.{Colors.END}")
        print(f"{Colors.GREEN}✅ Module Connector is ready for deployment.{Colors.END}")
    elif success_rate >= 70:
        print(f"{Colors.YELLOW}⚠️  Good, but some tests need attention.{Colors.END}")
        print(f"{Colors.YELLOW}🔧 Review failed tests before deployment.{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Multiple test failures detected.{Colors.END}")
        print(f"{Colors.RED}🚨 Fix critical issues before proceeding.{Colors.END}")
    
    # Exit with appropriate code
    exit_code = 0 if success_rate >= 90 else 1
    
    print(f"\n{Colors.BOLD}Exit Code: {exit_code}{Colors.END}")
    return exit_code

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️  Test suite interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}💥 Test runner error: {e}{Colors.END}")
        sys.exit(1)
