from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Runtime configuration loaded from environment variables (and optional .env).

    Keep it small: only things that must vary per environment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(min_length=8, description="Static API key for X-API-Key header")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@db:5432/postgres",
        description="SQLAlchemy async database URL",
    )
    debug: bool = Field(default=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
