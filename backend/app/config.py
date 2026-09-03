from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://grillme:change-me@localhost:5432/grillme"
    # No default: it signs the auth session cookie, so a stack started without SESSION_SECRET
    # must fail at startup rather than silently sign with a fallback every reader of this file
    # also knows (see .env.example, which still ships a placeholder to override).
    session_secret: str
    minio_endpoint: str = "localhost:9000"
    minio_root_user: str = "grillme"
    minio_root_password: str = "change-me-too"
    minio_bucket: str = "grillme"
    minio_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
