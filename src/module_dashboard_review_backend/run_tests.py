#!/usr/bin/env python3
"""
Test runner script for Dashboard Review Backend.

This script provides a convenient way to run different test suites
with appropriate configurations.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, env=None):
    """Run a command and return exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, env=env)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description='Run tests for Dashboard Review Backend'
    )
    
    parser.add_argument(
        'suite',
        choices=['all', 'unit', 'performance', 'concurrency', 'load', 
                'recovery', 'integration', 'coverage'],
        help='Test suite to run'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--parallel', '-n',
        action='store_true',
        help='Run tests in parallel'
    )
    
    parser.add_argument(
        '--failfast', '-x',
        action='store_true',
        help='Stop on first failure'
    )
    
    parser.add_argument(
        '--markers', '-m',
        help='Run tests matching given mark expression'
    )
    
    parser.add_argument(
        '--keyword', '-k',
        help='Run tests matching given keyword expression'
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ['pytest']
    
    # Add common options
    if args.verbose:
        cmd.append('-v')
    
    if args.failfast:
        cmd.append('-x')
    
    if args.parallel:
        cmd.extend(['-n', 'auto'])
    
    if args.markers:
        cmd.extend(['-m', args.markers])
    
    if args.keyword:
        cmd.extend(['-k', args.keyword])
    
    # Configure based on suite
    env = os.environ.copy()
    
    if args.suite == 'all':
        # Run all tests except integration (unless env vars are set)
        if not os.getenv('TEST_SUPABASE_URL'):
            cmd.extend(['-m', 'not integration'])
        cmd.append('tests/')
        
    elif args.suite == 'unit':
        # Run unit tests only
        cmd.extend(['tests/test_api', 'tests/test_services', 'tests/unit'])
        
    elif args.suite == 'performance':
        # Run performance tests
        cmd.extend(['tests/performance', '-m', 'performance', '-s'])
        
    elif args.suite == 'concurrency':
        # Run concurrency tests
        cmd.extend(['tests/concurrency', '-m', 'concurrency'])
        
    elif args.suite == 'load':
        # Run load tests
        cmd.extend(['tests/load', '-m', 'load', '-s'])
        print("\nNOTE: Load tests may take several minutes to complete")
        
    elif args.suite == 'recovery':
        # Run recovery tests
        cmd.extend(['tests/recovery', '-m', 'recovery'])
        
    elif args.suite == 'integration':
        # Run integration tests
        if not os.getenv('TEST_SUPABASE_URL'):
            print("\nERROR: Integration tests require TEST_SUPABASE_URL and TEST_SUPABASE_KEY")
            print("Set these environment variables to point to a test Supabase instance")
            return 1
        
        cmd.extend(['tests/integration', '-m', 'integration'])
        
    elif args.suite == 'coverage':
        # Run all tests with detailed coverage report
        cmd.extend([
            '--cov=src',
            '--cov-report=html',
            '--cov-report=term-missing',
            '--cov-report=json',
            'tests/'
        ])
        
        if not os.getenv('TEST_SUPABASE_URL'):
            cmd.extend(['-m', 'not integration'])
    
    # Run the tests
    exit_code = run_command(cmd, env)
    
    # Additional actions based on suite
    if args.suite == 'coverage' and exit_code == 0:
        print("\n" + "="*60)
        print("Coverage report generated!")
        print("HTML report: htmlcov/index.html")
        print("JSON report: coverage.json")
        print("="*60)
        
        # Optionally open HTML report
        if sys.platform == 'darwin':
            subprocess.run(['open', 'htmlcov/index.html'])
        elif sys.platform == 'linux':
            subprocess.run(['xdg-open', 'htmlcov/index.html'])
        elif sys.platform == 'win32':
            subprocess.run(['start', 'htmlcov/index.html'], shell=True)
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
