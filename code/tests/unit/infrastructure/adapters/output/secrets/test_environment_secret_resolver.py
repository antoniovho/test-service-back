import pytest

from test_service.domain.model.exceptions.secret_resolution_exception import (
    SecretResolutionException,
)
from test_service.domain.model.execution.environment import SecretReference
from test_service.infrastructure.adapters.output.secrets.environment_secret_resolver import (
    EnvironmentSecretResolver,
)


class TestEnvironmentSecretResolver:
    async def test_when_prefixed_variable_exists_expect_its_value(self) -> None:
        resolver = EnvironmentSecretResolver(environ={"TEST_SERVICE_SECRET_API_KEY": "the-value"})

        value = await resolver.resolve_secret(SecretReference("env", "API_KEY"))

        assert value == "the-value"

    async def test_when_no_environment_is_injected_expect_process_environment_read(
        self, monkeypatch
    ) -> None:
        monkeypatch.setenv("TEST_SERVICE_SECRET_API_KEY", "process-value")

        value = await EnvironmentSecretResolver().resolve_secret(SecretReference("env", "API_KEY"))

        assert value == "process-value"

    async def test_when_custom_prefix_is_configured_expect_it_used(self) -> None:
        resolver = EnvironmentSecretResolver(prefix="E2E_", environ={"E2E_TOKEN": "custom"})

        value = await resolver.resolve_secret(SecretReference("env", "TOKEN"))

        assert value == "custom"

    @pytest.mark.parametrize(
        "key",
        ["DATABASE_PASSWORD", "XRAY_CLIENT_SECRET", "JIRA_API_TOKEN", "PATH"],
    )
    async def test_when_key_names_a_service_credential_expect_it_unreachable(self, key) -> None:
        resolver = EnvironmentSecretResolver(environ={key: "service-credential"})

        with pytest.raises(SecretResolutionException) as exc:
            await resolver.resolve_secret(SecretReference("env", key))

        assert exc.value.code == "SECRET_RESOLUTION_FAILED"
        assert "service-credential" not in exc.value.error_description

    @pytest.mark.parametrize("provider", ["vault", "ENV", "aws"], ids=["vault", "uppercase", "aws"])
    async def test_when_provider_is_not_supported_expect_exception(self, provider) -> None:
        resolver = EnvironmentSecretResolver(environ={"TEST_SERVICE_SECRET_API_KEY": "value"})

        with pytest.raises(SecretResolutionException, match="provider is not supported") as exc:
            await resolver.resolve_secret(SecretReference(provider, "API_KEY"))

        assert provider not in exc.value.error_description

    @pytest.mark.parametrize(
        "key",
        ["api_key", "../API_KEY", "API KEY", "1KEY", "API-KEY", "API\n", "API_KEY/.."],
        ids=["lowercase", "traversal", "space", "leading-digit", "hyphen", "newline", "suffix"],
    )
    async def test_when_key_format_is_invalid_expect_exception_without_echo(self, key) -> None:
        resolver = EnvironmentSecretResolver(environ={"TEST_SERVICE_SECRET_API_KEY": "value"})

        with pytest.raises(SecretResolutionException, match="invalid format") as exc:
            await resolver.resolve_secret(SecretReference("env", key))

        assert key not in exc.value.error_description

    @pytest.mark.parametrize(
        "environ", [{}, {"TEST_SERVICE_SECRET_API_KEY": ""}], ids=["missing", "empty"]
    )
    async def test_when_variable_is_missing_or_empty_expect_exception(self, environ) -> None:
        resolver = EnvironmentSecretResolver(environ=environ)

        with pytest.raises(SecretResolutionException, match="not available"):
            await resolver.resolve_secret(SecretReference("env", "API_KEY"))
