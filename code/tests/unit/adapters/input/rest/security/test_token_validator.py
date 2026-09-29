import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from test_service.config import AuthSettings
from test_service.infrastructure.adapters.input.rest.security.token_validator import (
    InvalidTokenError,
    JwtTokenValidator,
    MockTokenValidator,
    get_token_validator,
)


@pytest.fixture(autouse=True)
def _clear_validator_cache():
    get_token_validator.cache_clear()
    yield
    get_token_validator.cache_clear()


class TestMockTokenValidator:
    def test_when_token_is_not_jwt_shaped_expect_fixed_demo_subject(self):
        validator = MockTokenValidator()

        claims = validator.get_claims("not-a-jwt")

        assert claims == {"sub": "mock-user@example.com"}

    def test_when_token_carries_a_sub_claim_expect_that_subject(self):
        validator = MockTokenValidator()
        token = jwt.encode(
            {"sub": "alice@example.com"}, "unused-secret-at-least-32-bytes-long", algorithm="HS256"
        )

        claims = validator.get_claims(token)

        assert claims == {"sub": "alice@example.com"}

    def test_when_payload_segment_is_not_valid_base64_json_expect_fixed_demo_subject(self):
        validator = MockTokenValidator()

        claims = validator.get_claims("header.not-valid-base64-json.signature")

        assert claims == {"sub": "mock-user@example.com"}


class TestGetTokenValidator:
    def test_when_mock_enabled_expect_mock_token_validator(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("AUTH_MOCK_ENABLED", "true")

        assert isinstance(get_token_validator(), MockTokenValidator)

    def test_when_mock_disabled_expect_jwt_token_validator(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("AUTH_MOCK_ENABLED", "false")
        monkeypatch.setenv("AUTH_JWKS_URL", "https://issuer.example.com/.well-known/jwks.json")

        assert isinstance(get_token_validator(), JwtTokenValidator)


class TestJwtTokenValidator:
    def test_when_jwks_url_missing_expect_value_error(self):
        with pytest.raises(ValueError, match="AUTH_JWKS_URL"):
            JwtTokenValidator(AuthSettings(mock_enabled=False, jwks_url=None))

    def test_when_token_signature_is_valid_expect_claims_returned(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        now = int(time.time())
        token = jwt.encode(
            {
                "sub": "alice@example.com",
                "iss": "https://issuer.example.com",
                "aud": "test-service",
                "iat": now,
                "exp": now + 3600,
            },
            private_key,
            algorithm="RS256",
        )
        validator = JwtTokenValidator(
            AuthSettings(
                mock_enabled=False,
                issuer="https://issuer.example.com",
                audience="test-service",
                jwks_url="https://issuer.example.com/.well-known/jwks.json",
            )
        )
        monkeypatch.setattr(
            validator._jwk_client,
            "get_signing_key_from_jwt",
            lambda _token: type("SigningKey", (), {"key": public_key})(),
        )

        claims = validator.get_claims(token)

        assert claims["sub"] == "alice@example.com"

    def test_when_token_is_expired_expect_invalid_token_error(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        expired_at = int(time.time()) - 3600
        token = jwt.encode(
            {"sub": "alice@example.com", "iat": expired_at - 60, "exp": expired_at},
            private_key,
            algorithm="RS256",
        )
        validator = JwtTokenValidator(
            AuthSettings(
                mock_enabled=False, jwks_url="https://issuer.example.com/.well-known/jwks.json"
            )
        )
        monkeypatch.setattr(
            validator._jwk_client,
            "get_signing_key_from_jwt",
            lambda _token: type("SigningKey", (), {"key": public_key})(),
        )

        with pytest.raises(InvalidTokenError):
            validator.get_claims(token)
