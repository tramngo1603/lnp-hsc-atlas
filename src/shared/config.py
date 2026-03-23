"""Application configuration loaded from environment variables.

Uses python-dotenv to load .env and exposes settings as a validated
Pydantic model. All secrets come from the environment — never hardcoded.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

# Project root is three levels up from this file: src/shared/config.py -> project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    anthropic_api_key: str = ""
    ncbi_api_key: str = ""
    ncbi_email: str = ""
    database_url: str = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'data' / 'lnp_research.db'}"
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and return application settings.

    Reads from .env file at project root, then environment variables.
    Cached after first call — use ``get_settings.cache_clear()`` in tests.

    Returns:
        Validated Settings instance.
    """
    load_dotenv(PROJECT_ROOT / ".env")
    return Settings(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        ncbi_api_key=os.getenv("NCBI_API_KEY", ""),
        ncbi_email=os.getenv("NCBI_EMAIL", ""),
        database_url=os.getenv(
            "DATABASE_URL",
            f"sqlite+aiosqlite:///{PROJECT_ROOT / 'data' / 'lnp_research.db'}",
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
