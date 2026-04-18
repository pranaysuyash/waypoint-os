"""
tests.conftest — Pytest configuration and fixtures.

This file sets up the Python path for pytest to find the src modules.
"""

import sys
from pathlib import Path

import pytest

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

# Add spine-api directory so unit tests can import run_state / run_ledger / run_events
spine_api_dir = Path(__file__).parent.parent / "spine-api"
if str(spine_api_dir) not in sys.path:
    sys.path.insert(0, str(spine_api_dir))


def pytest_configure(config):
    """Register custom marks to avoid PytestUnknownMarkWarning."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require a live spine-api instance (skip with -m 'not integration')",
    )
