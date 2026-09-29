"""Bearer token validation for the inbound identity middleware."""

import base64
import json
from functools import lru_cache
from typing import Protocol

import jwt
from jwt import PyJWKClient

from test_service.config import AuthSettings

_REQUIRED_CLAIMS = ["sub", "iat", "exp"]
_ALGORITHMS = ["RS256", "ES256"]


class InvalidTokenError(Exception):
    """Raised when a bearer token is missing, malformed, or fails validation."""


class TokenValidator(Protocol):
    """Resolves the claims carried by a bearer token."""

    def get_claims(self, token: str) -> dict[str, object]:
        """Return the claims of a bearer token.

        Raises:
            InvalidTokenError: If the token is malformed or fails validation.
        """
        ...


class JwtTokenValidator:
    """Validates bearer tokens against a remote JWKS endpoint using PyJWT."""

    def __init__(self, settings: AuthSettings) -> None:
        if not settings.jwks_url:
            raise ValueError("AUTH_JWKS_URL must be configured when AUTH_MOCK_ENABLED is false")
        self._settings = settings
        self._jwk_client = PyJWKClient(settings.jwks_url)

    def get_claims(self, token: str) -> dict[str, object]:
        """Verify the token signature and standard claims against the JWKS endpoint."""
        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=_ALGORITHMS,
                issuer=self._settings.issuer,
                audience=self._settings.audience,
                options={"require": _REQUIRED_CLAIMS},
            )
        except jwt.PyJWTError as exc:
            raise InvalidTokenError(str(exc)) from exc


class MockTokenValidator:
    """Demo validator that never verifies the token signature.

    Mirrors the mocked-identity pattern used for local demos:
    a fixed identity is used instead of contacting a real identity
    provider, so the API is usable without a configured JWKS endpoint.
    """

    _MOCK_SUBJECT = "mock-user@example.com"

    def get_claims(self, token: str) -> dict[str, object]:
        """Return the unverified `sub` claim if present, else a fixed demo identity."""
        return {"sub": _decode_unverified_subject(token) or self._MOCK_SUBJECT}


def _decode_unverified_subject(token: str) -> str | None:
    """Best-effort, unverified extraction of the `sub` claim from a JWT-shaped string."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    payload_segment = parts[1]
    padding = "=" * (-len(payload_segment) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_segment + padding))
    except ValueError:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None


@lru_cache(maxsize=1)
def get_token_validator() -> TokenValidator:
    """Return the process-wide token validator, selected by `AuthSettings`."""
    settings = AuthSettings()
    if settings.mock_enabled:
        return MockTokenValidator()
    return JwtTokenValidator(settings)
