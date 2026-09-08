"""
DrishtiGIS — Application Settings
====================================
All secrets and configuration loaded from environment variables.
No secrets are hard-coded.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "DrishtiGIS API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database — PostgreSQL + PostGIS (Supabase or self-hosted)
    # Falls back to SQLite for local dev without a PostGIS instance.
    DATABASE_URL: str = "sqlite+aiosqlite:///./drishtigis_dev.db"

    # Supabase (optional — used when DATABASE_URL points to Supabase)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Gemini (AI assistant — Phase 3)
    GEMINI_API_KEY: str = ""

    # JWT signing key
    SECRET_KEY: str = "dev-insecure-key-change-before-production"

    # CORS — comma-separated list of allowed frontend origins
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]


settings = Settings()
