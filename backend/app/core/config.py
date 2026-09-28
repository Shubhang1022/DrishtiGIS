"""
DrishtiGIS — Application Settings
====================================
All secrets and configuration loaded from environment variables.
No secrets are hard-coded.
"""

from typing import List, Any, Union
from pydantic import field_validator
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

    # Gemini / LLM (AI assistant)
    GEMINI_API_KEY: str = ""
    LLM_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    LLM_PROVIDER: str = "openrouter"
    LLM_MODEL: str = "google/gemini-2.5-flash"

    # JWT signing key — MUST be overridden with a random secret in production
    SECRET_KEY: str = "dev-insecure-key-change-before-production"

    # Production Demo Account Flag — Set to False in production to disable privileged demo seeds
    ENABLE_DEMO_ACCOUNTS: bool = True

    # Cookie Security Settings for HTTPS
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # CORS — comma-separated list or JSON array of allowed frontend origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                try:
                    return json.loads(v_str)
                except Exception:
                    pass
            return [origin.strip() for origin in v_str.split(",") if origin.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Maximum dataset upload size in MB (default 100 MB)
    MAX_UPLOAD_SIZE_MB: int = 100


settings = Settings()
