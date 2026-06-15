from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Veilbound Tides API"
    environment: str = "local"
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


def validate_runtime_settings(settings: Settings) -> None:
    if settings.environment.lower() not in {"local", "test", "staging", "production"}:
        raise RuntimeError("VT_ENVIRONMENT must be local, test, staging, or production")

    if settings.environment.lower() == "production":
        if settings.jwt_secret == "change-me-in-production":
            raise RuntimeError("VT_JWT_SECRET must be changed before production startup")
        if "://game:game@" in settings.database_url:
            raise RuntimeError("VT_DATABASE_URL must not use scaffold database credentials")
        if settings.debug:
            raise RuntimeError("VT_DEBUG must be false in production")

    if settings.jwt_access_token_minutes < 5 or settings.jwt_access_token_minutes > 60:
        raise RuntimeError("VT_JWT_ACCESS_TOKEN_MINUTES must be between 5 and 60")
