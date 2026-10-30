"""
ECONODE Studio - Comprehensive E2E Test Suite Runner (run_all_e2e.py)
Discovers and executes all 4 Tiers of tests:
- Tier 1: Feature Coverage (F01 - F20, 100 tests)
- Tier 2: Boundary & Corner Cases (F01 - F20, 100 tests)
- Tier 3: Cross-Feature Combinations (15 tests)
- Tier 4: Real-World Scenarios (10 tests)
Total: 225 automated E2E tests.
"""

import sys
import os
import time
import unittest

# Ensure proper encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    print("=" * 70)
    print("  ECONODE STUDIO — AUTOMATED E2E TEST SUITE RUNNER")
    print("=" * 70)
    print(f"Target Server: {os.environ.get('ECONODE_SERVER_URL', 'http://127.0.0.1:8095')}")
    print(f"Test Suite Directory: {SCRIPT_DIR}\n")

    loader = unittest.TestLoader()
    start_time = time.time()

    # Load suites explicitly by module
    from tests.e2e.test_tier1_features import TestTier1FeatureCoverage
    from tests.e2e.test_tier2_boundaries import TestTier2BoundariesAndCornerCases
    from tests.e2e.test_tier3_combinations import TestTier3CrossFeatureCombinations
    from tests.e2e.test_tier4_scenarios import TestTier4RealWorldScenarios

    suite1 = loader.loadTestsFromTestCase(TestTier1FeatureCoverage)
    suite2 = loader.loadTestsFromTestCase(TestTier2BoundariesAndCornerCases)
    suite3 = loader.loadTestsFromTestCase(TestTier3CrossFeatureCombinations)
    suite4 = loader.loadTestsFromTestCase(TestTier4RealWorldScenarios)

    full_suite = unittest.TestSuite([suite1, suite2, suite3, suite4])

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(full_suite)
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("  E2E TEST EXECUTION SUMMARY")
    print("=" * 70)
    print(f"  Tier 1 (Feature Coverage):     {suite1.countTestCases():3d} tests")
    print(f"  Tier 2 (Boundary & Corner):    {suite2.countTestCases():3d} tests")
    print(f"  Tier 3 (Cross-Feature Combos): {suite3.countTestCases():3d} tests")
    print(f"  Tier 4 (Real-World Scenarios): {suite4.countTestCases():3d} tests")
    print("  " + "-" * 50)
    print(f"  Total Tests Executed:          {result.testsRun:3d} tests")
    print(f"  Passed:                        {result.testsRun - len(result.failures) - len(result.errors):3d}")
    print(f"  Failed:                        {len(result.failures):3d}")
    print(f"  Errors:                        {len(result.errors):3d}")
    print(f"  Elapsed Time:                  {elapsed:.3f} seconds")
    print("=" * 70)

    if result.wasSuccessful():
        print(">>> RESULT: ALL E2E TESTS PASSED (100% SUCCESS RATE)\n")
        sys.exit(0)
    else:
        print(">>> RESULT: TEST RUN FAILED\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
