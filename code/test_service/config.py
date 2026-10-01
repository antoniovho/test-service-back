"""Environment-driven configuration for the Test Service application."""

from pydantic import Field, SecretStr
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


class PostgresDatabaseSettings(BaseSettings):
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


class XraySettings(BaseSettings):
    """Xray Cloud integration settings loaded from ``.env``.

    The projection and drift URLs deliberately remain configurable because the
    concrete Xray workflow is tenant-specific. Credentials are never logged or
    exposed through REST responses.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="XRAY_",
        extra="ignore",
    )

    client_id: str
    client_secret: SecretStr
    auth_url: str = "https://xray.cloud.getxray.app/api/v2/authenticate"
    projection_url: str
    drift_check_url: str
    timeout_seconds: float = 10.0
    max_attempts: int = 3
    retry_backoff_seconds: float = 0.25


class ViewerSettings(BaseSettings):
    """Configuration for durable Viewer operation processing."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="VIEWER_",
        extra="ignore",
    )

    operation_recovery_timeout_seconds: int = Field(default=1800, gt=0)


class JiraSettings(BaseSettings):
    """Configuration of Jira as the V1 external project validator."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="JIRA_", extra="ignore"
    )

    base_url: str
    user_email: str
    api_token: SecretStr
    timeout_seconds: float = 10.0
