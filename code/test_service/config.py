"""Environment-driven configuration for the Test Service application."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class AuthSettings(BaseSettings):
    """Bearer token validation settings.

    No `AUTH_*` variables exist yet in this repo's deployment configmap — add
    them wherever the real configmap is generated once this stops being a demo.
    Mirrors the shape of Amiga's `amiga.authentication.jwt.*` configuration
    (`server.url` -> `jwks_url`, `localtest.enabled` -> `mock_enabled`).

    Args:
        mock_enabled: When true, bypasses signature verification and returns a
            fixed demo identity. Defaults to true so the service is usable
            without a configured identity provider.
        issuer: Expected `iss` claim. When unset, the issuer is not checked.
        audience: Expected `aud` claim. When unset, the audience is not checked.
        jwks_url: JWKS endpoint used to resolve signing keys. Required when
            `mock_enabled` is false.
    """

    model_config = SettingsConfigDict(env_prefix="AUTH_")

    mock_enabled: bool = True
    issuer: str | None = None
    audience: str | None = None
    jwks_url: str | None = None


class DatabaseSettings(BaseSettings):
    """PostgreSQL connection settings loaded from the runtime environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DATABASE_",
        extra="ignore",
    )

    host: str
    port: int
    name: str
    user: str
    password: SecretStr
    pool_size: int = 5
    max_overflow: int = 10

    @property
    def connection_url(self) -> URL:
        """Build the async SQLAlchemy URL without exposing it through configuration logs."""
        return URL.create(
            "postgresql+asyncpg",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.name,
        )
