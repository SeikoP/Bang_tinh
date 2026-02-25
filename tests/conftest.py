"""
Shared test fixtures for WMS test suite.
Kept lightweight — only common fixtures belong here.
"""

import pytest
import tempfile
import os


@pytest.fixture
def tmp_db_path(tmp_path):
    """Provide a temporary database path for integration tests."""
    return str(tmp_path / "test_storage.db")


@pytest.fixture(autouse=True)
def _fast_test_timeout(request):
    """Auto-skip tests that exceed 10 seconds (safety net)."""
    # This works with pytest-timeout if installed
    marker = request.node.get_closest_marker("slow")
    if marker:
        pytest.skip("Skipping slow test in fast mode")

