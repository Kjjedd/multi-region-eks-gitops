from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    db_host: str = Field(default="localhost")
    db_port: int = Field(default=3306)
    db_user: str = Field(default="boarduser")
    db_password: str = Field(default="boardpass")
    db_name: str = Field(default="boarddb")

    app_region: str = Field(default="unknown")
    app_env: str = Field(default="local")
    app_version: str = Field(default="dev")
    app_commit: str = Field(default="unknown")
    log_level: str = Field(default="INFO")

    cors_allow_origins: str = Field(default="")

    database_url_override: str | None = Field(default=None)

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return (
            f"mysql+asyncmy://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.cors_allow_origins:
            return []
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
