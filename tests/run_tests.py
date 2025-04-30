#!/usr/bin/env python3
"""
Test Runner for Spidy Browser

Executes all unit tests and generates a report.
"""

import unittest
import sys
import os
from datetime import datetime

def run_tests():
    """Run all tests and generate report"""
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Start test run
    print(f"\nRunning Spidy Browser Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    # Create test runner with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run tests and capture results
    result = runner.run(suite)
    
    # Print summary
    print("\nTest Summary:")
    print("-" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100:.1f}%")
    print("-" * 70)
    
    # Print failure details if any
    if result.failures or result.errors:
        print("\nFailure Details:")
        for failure in result.failures:
            print(f"\nTest: {failure[0]}")
            print(f"Error: {failure[1]}")
        for error in result.errors:
            print(f"\nTest: {error[0]}")
            print(f"Error: {error[1]}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(not success)
