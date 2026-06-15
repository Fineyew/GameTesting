from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Veilbound Tides API"
    api_version: str = "0.1.0"
    minimum_client_version: str = "0.1.0"
    content_manifest_version: str = "1"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://game:game@postgres:5432/game"
    jwt_issuer: str = "veilbound-tides"
    jwt_audience: str = "veilbound-tides-client"
    jwt_secret: str = "change-me-in-production"
    jwt_access_token_minutes: int = 15
    content_root: Path = Path(__file__).resolve().parents[3] / "content"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VT_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
