"""
AgroTwin AI - Test Runner
==========================

Single command to run the full backend test suite.

Usage:
    python scripts/run_tests.py

Or from agrotwin_api:
    python -m pytest tests/ -v
"""

import os
import subprocess
import sys


def main():
    api_root = os.path.join(os.path.dirname(__file__), "..", "agrotwin_api")
    api_root = os.path.abspath(api_root)

    print("=" * 80)
    print("  AgroTwin AI - Full Test Suite")
    print("=" * 80)
    print(f"  API Root: {api_root}")
    print()

    # Run pytest
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=api_root,
    )

    if result.returncode == 0:
        print("\n" + "=" * 80)
        print("  ALL TESTS PASSED")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("  SOME TESTS FAILED")
        print("=" * 80)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
