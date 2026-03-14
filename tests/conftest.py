"""Shared pytest fixtures for the test suite.

Add fixtures here that are used across multiple test files.
File-specific fixtures belong in the individual test file.
"""

import pytest


@pytest.fixture
def required_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set all required environment variables for tests that load Settings."""
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("EODHD_API_KEY", "test_eodhd_key")
    monkeypatch.setenv("ALPACA_API_KEY", "test_alpaca_key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "test_alpaca_secret")
