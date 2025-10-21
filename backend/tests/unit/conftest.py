"""
Pytest Configuration for Unit Tests
EPL Match Predictor v3.0
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))


@pytest.fixture
def assert_near():
    """Helper to assert values are nearly equal"""
    def _assert_near(actual, expected, tolerance=0.01):
        """
        Assert two values are within tolerance

        Args:
            actual: Actual value
            expected: Expected value
            tolerance: Absolute tolerance (default 0.01)
        """
        assert abs(actual - expected) < tolerance, \
            f"Expected {expected}, got {actual} (diff: {abs(actual - expected)})"

    return _assert_near
