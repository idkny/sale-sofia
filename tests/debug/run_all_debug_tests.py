#!/usr/bin/env python3
"""
Debug Test Runner

Runs all isolated debug tests in sequence.
Run: python tests/debug/run_all_debug_tests.py

Options:
  --quick     Run only fast isolated tests (skip full pipeline)
  --full      Run all tests including full pipeline (10-20 min)
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
TEST_DIR = Path(__file__).parent


def run_test(test_name: str, test_file: Path) -> bool:
    """Run a single test file and return pass/fail."""
    print(f"\n{'=' * 60}")
    print(f"RUNNING: {test_name}")
    print('=' * 60)

    result = subprocess.run(
        [sys.executable, str(test_file)],
        cwd=PROJECT_ROOT
    )

    return result.returncode == 0


def main():
    """Run debug tests."""
    quick_mode = "--quick" in sys.argv or "--full" not in sys.argv

    print("=" * 60)
    print("DEBUG TEST RUNNER")
    print(f"Mode: {'QUICK (isolated only)' if quick_mode else 'FULL (all tests)'}")
    print("=" * 60)

    # Define tests
    isolated_tests = [
        ("Redis Isolated", TEST_DIR / "test_redis_isolated.py"),
        ("Celery Isolated", TEST_DIR / "test_celery_isolated.py"),
        ("Mubeng Isolated", TEST_DIR / "test_mubeng_isolated.py"),
        ("PSC Isolated", TEST_DIR / "test_psc_isolated.py"),
    ]

    integration_tests = [
        ("Full Pipeline", TEST_DIR / "test_full_pipeline.py"),
    ]

    results = []

    # Run isolated tests
    print("\n" + "=" * 60)
    print("PHASE 1: ISOLATED COMPONENT TESTS")
    print("=" * 60)

    for name, test_file in isolated_tests:
        passed = run_test(name, test_file)
        results.append((name, passed))

        # Stop if isolated test fails
        if not passed:
            print(f"\n[STOP] {name} failed - fix before continuing")
            break

    # Run integration tests only if all isolated tests passed and not quick mode
    if all(r[1] for r in results) and not quick_mode:
        print("\n" + "=" * 60)
        print("PHASE 2: INTEGRATION TESTS")
        print("=" * 60)

        for name, test_file in integration_tests:
            passed = run_test(name, test_file)
            results.append((name, passed))

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        marker = "  " if passed else ">>"
        print(f"{marker} {name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED")
        if quick_mode:
            print("(Run with --full for integration tests)")
        return 0
    else:
        print("SOME TESTS FAILED")
        print("Fix failing tests before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(main())
