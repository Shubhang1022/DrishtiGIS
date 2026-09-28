"""
DrishtiGIS — Application Settings
====================================
All secrets and configuration loaded from environment variables.
No secrets are hard-coded.
"""

from pathlib import Path
from typing import List, Any, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Robust, project-relative environment file resolution.
# Resolves paths relative to this config file so loading works whether the application
# is started from the repository root (/home/ubuntu/DrishtiGIS), backend/ (/home/ubuntu/DrishtiGIS/backend),
# or any arbitrary working directory.
_CONFIG_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _CONFIG_DIR.parent.parent
_REPO_ROOT = _BACKEND_DIR.parent

_ENV_FILES = (
    _REPO_ROOT / ".env",
    _BACKEND_DIR / ".env",
    ".env",
    "backend/.env",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
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

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def assemble_database_url(cls, v: str) -> str:
        """
        Normalize database URLs for SQLAlchemy async engine:
        - Supabase / standard PostgreSQL URLs starting with 'postgresql://' or 'postgres://'
          are normalized to 'postgresql+asyncpg://'.
        - Local development SQLite URLs starting with 'sqlite:///'
          are normalized to 'sqlite+aiosqlite:///'.
        """
        if not v:
            return v
        v_str = str(v).strip()
        if v_str.startswith("postgres://"):
            return "postgresql+asyncpg://" + v_str[len("postgres://"):]
        if v_str.startswith("postgresql://"):
            return "postgresql+asyncpg://" + v_str[len("postgresql://"):]
        if v_str.startswith("sqlite:///"):
            return "sqlite+aiosqlite:///" + v_str[len("sqlite:///"):]
        return v_str

    # Supabase (optional — used when DATABASE_URL points to Supabase)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Gemini / LLM (AI assistant)
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-2.5-flash"

    # JWT signing key — MUST be overridden with a random secret in production
    SECRET_KEY: str = "dev-insecure-key-change-before-production"

    # Production Demo Account Flag — Set to False in production to disable privileged demo seeds
    ENABLE_DEMO_ACCOUNTS: bool = True

    # Cookie Security Settings for HTTPS
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # CORS — comma-separated list or JSON array of allowed frontend origins.
    # Using Union[List[str], str] prevents pydantic-settings from pre-decoding as JSON
    # before our field_validator handles comma-separated strings.
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                try:
                    loaded = json.loads(v_str)
                    if isinstance(loaded, list):
                        return [str(origin).strip() for origin in loaded if str(origin).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v_str.split(",") if origin.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Maximum dataset upload size in MB (default 100 MB)
    MAX_UPLOAD_SIZE_MB: int = 100


settings = Settings()
