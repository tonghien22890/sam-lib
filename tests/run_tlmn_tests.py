#!/usr/bin/env python3
"""
Run TLMN AI Tests

Script to run comprehensive tests for TLMN AI implementation.
"""

import sys
import os
import unittest
from typing import List, Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def run_tlmn_tests() -> Dict[str, Any]:
    """
    Run TLMN AI tests and return results.
    
    Returns:
        Dict containing test results
    """
    print("🧪 Running TLMN AI Tests...")
    print("=" * 50)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('ai_common.tests.test_tlmn_ai')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Compile results
    test_results = {
        'total_tests': result.testsRun,
        'passed': result.testsRun - len(result.failures) - len(result.errors),
        'failed': len(result.failures),
        'errors': len(result.errors),
        'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
        'failures': [str(f[1]) for f in result.failures],
        'errors': [str(e[1]) for e in result.errors]
    }
    
    return test_results

def print_test_summary(results: Dict[str, Any]) -> None:
    """
    Print test summary.
    
    Args:
        results: Test results
    """
    print("\n" + "=" * 50)
    print("📊 TLMN AI Test Results:")
    print("=" * 50)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Errors: {results['errors']}")
    print(f"Success Rate: {results['success_rate']:.1%}")
    
    if results['failures']:
        print(f"\n❌ Failures ({len(results['failures'])}):")
        for i, failure in enumerate(results['failures'], 1):
            print(f"  {i}. {failure}")
    
    if results['errors']:
        print(f"\n💥 Errors ({len(results['errors'])}):")
        for i, error in enumerate(results['errors'], 1):
            print(f"  {i}. {error}")
    
    if results['success_rate'] == 1.0:
        print("\n🎉 All tests passed!")
    elif results['success_rate'] >= 0.8:
        print("\n✅ Most tests passed!")
    else:
        print("\n⚠️  Some tests failed!")

def main():
    """Main function"""
    try:
        # Run tests
        results = run_tlmn_tests()
        
        # Print summary
        print_test_summary(results)
        
        # Exit with appropriate code
        if results['success_rate'] == 1.0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
