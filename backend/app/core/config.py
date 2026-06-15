import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlparse

PLACEHOLDER_TOKENS = (
    "change-me",
    "change-this",
    "changeme",
    "example",
    "placeholder",
    "password",
    "secret",
)


@dataclass(frozen=True)
class Settings:
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
    database_pool_size: int = 5
    database_max_overflow: int = 5
    content_root: Path = Path(__file__).resolve().parents[3] / "content"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            project_name=_env_str("VT_PROJECT_NAME", cls.project_name),
            environment=_env_str("VT_ENVIRONMENT", cls.environment),
            api_version=_env_str("VT_API_VERSION", cls.api_version),
            minimum_client_version=_env_str(
                "VT_MINIMUM_CLIENT_VERSION",
                cls.minimum_client_version,
            ),
            content_manifest_version=_env_str(
                "VT_CONTENT_MANIFEST_VERSION",
                cls.content_manifest_version,
            ),
            debug=_env_bool("VT_DEBUG", cls.debug),
            database_url=_env_str("VT_DATABASE_URL", cls.database_url),
            jwt_issuer=_env_str("VT_JWT_ISSUER", cls.jwt_issuer),
            jwt_audience=_env_str("VT_JWT_AUDIENCE", cls.jwt_audience),
            jwt_secret=_env_str("VT_JWT_SECRET", cls.jwt_secret),
            jwt_access_token_minutes=_env_int(
                "VT_JWT_ACCESS_TOKEN_MINUTES",
                cls.jwt_access_token_minutes,
            ),
            database_pool_size=_env_int("VT_DATABASE_POOL_SIZE", cls.database_pool_size),
            database_max_overflow=_env_int(
                "VT_DATABASE_MAX_OVERFLOW",
                cls.database_max_overflow,
            ),
            content_root=Path(_env_str("VT_CONTENT_ROOT", str(cls.content_root))),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return int(raw_value)


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def validate_runtime_settings(settings: Settings) -> None:
    environment = settings.environment.lower()
    if environment not in {"local", "test", "staging", "production"}:
        raise RuntimeError("VT_ENVIRONMENT must be local, test, staging, or production")

    if environment in {"staging", "production"}:
        _validate_non_placeholder_secret("VT_JWT_SECRET", settings.jwt_secret, min_length=32)
        _validate_database_url(settings.database_url)
        if settings.debug:
            raise RuntimeError("VT_DEBUG must be false outside local/test environments")

    if settings.jwt_access_token_minutes < 5 or settings.jwt_access_token_minutes > 60:
        raise RuntimeError("VT_JWT_ACCESS_TOKEN_MINUTES must be between 5 and 60")

    if settings.database_pool_size < 1 or settings.database_pool_size > 20:
        raise RuntimeError("VT_DATABASE_POOL_SIZE must be between 1 and 20")
    if settings.database_max_overflow < 0 or settings.database_max_overflow > 20:
        raise RuntimeError("VT_DATABASE_MAX_OVERFLOW must be between 0 and 20")


def _validate_non_placeholder_secret(name: str, value: str, min_length: int) -> None:
    normalized = value.strip().lower()
    if len(value.strip()) < min_length:
        raise RuntimeError(f"{name} must be at least {min_length} characters")
    if any(token in normalized for token in PLACEHOLDER_TOKENS):
        raise RuntimeError(f"{name} must not use placeholder text")


def _validate_database_url(database_url: str) -> None:
    parsed = urlparse(database_url)
    username = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    if username == "game":
        raise RuntimeError("VT_DATABASE_URL must not use scaffold database username")
    _validate_non_placeholder_secret("database password", password, min_length=16)
