"""
Root conftest.py for backend tests.

This file makes common fixtures available to all test files.
"""
# Import common fixtures so they're available to all tests
pytest_plugins = [
    "common.tests.conftest",
]
