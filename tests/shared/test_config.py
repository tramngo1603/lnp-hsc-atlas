"""Tests for shared.config — settings loading from environment."""

import os
from unittest.mock import patch

from shared.config import Settings, get_settings


class TestSettings:
    """Test the Settings Pydantic model."""

    def test_default_values(self) -> None:
        s = Settings()
        assert s.anthropic_api_key == ""
        assert s.ncbi_api_key == ""
        assert s.ncbi_email == ""
        assert "lnp_research.db" in s.database_url
        assert s.log_level == "INFO"

    def test_custom_values(self) -> None:
        s = Settings(
            anthropic_api_key="sk-test",
            ncbi_api_key="ncbi-test",
            ncbi_email="test@example.com",
            database_url="sqlite+aiosqlite:///custom.db",
        )
        assert s.anthropic_api_key == "sk-test"
        assert s.database_url == "sqlite+aiosqlite:///custom.db"


class TestGetSettings:
    """Test the get_settings() factory function."""

    def test_loads_from_environment(self) -> None:
        get_settings.cache_clear()
        env = {
            "ANTHROPIC_API_KEY": "sk-env-test",
            "NCBI_API_KEY": "ncbi-env",
            "NCBI_EMAIL": "env@example.com",
            "DATABASE_URL": "sqlite+aiosqlite:///env.db",
            "LOG_LEVEL": "DEBUG",
        }
        with patch.dict(os.environ, env, clear=False):
            settings = get_settings()
            assert settings.anthropic_api_key == "sk-env-test"
            assert settings.ncbi_api_key == "ncbi-env"
            assert settings.ncbi_email == "env@example.com"
            assert settings.database_url == "sqlite+aiosqlite:///env.db"
            assert settings.log_level == "DEBUG"
        get_settings.cache_clear()

    def test_caching(self) -> None:
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
        get_settings.cache_clear()
