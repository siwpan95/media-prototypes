"""Unified test runner — now delegates to pytest.

All test modules in tests/ are pytest-compatible.
Run directly:
    pytest tests/ -v

Or via this script (for backwards compatibility):
    python run_tests.py          # all tests
    python run_tests.py -k rule  # only rule tests
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest


def main():
    """Run tests via pytest."""
    sys.exit(pytest.main(["tests", "-v", "--tb=short"]))


if __name__ == "__main__":
    main()
