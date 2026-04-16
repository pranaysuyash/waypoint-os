"""
tests.conftest — Pytest configuration and fixtures.

This file sets up the Python path for pytest to find the src modules.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))
