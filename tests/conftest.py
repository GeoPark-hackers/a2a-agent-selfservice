"""Pytest configuration and fixtures."""

import os
import pytest


@pytest.fixture(autouse=True)
def set_test_env():
    """Set test environment variables."""
    os.environ["APP_ENV"] = "development"
    os.environ["APP_DEBUG"] = "true"
    os.environ["LLM_PROVIDER"] = "google_ai"
    os.environ["GOOGLE_API_KEY"] = "test-key"
    yield
