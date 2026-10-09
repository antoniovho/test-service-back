from types import MappingProxyType
from unittest.mock import AsyncMock

import pytest

from test_service.domain.application.services.execution.execution_variables_resolver import (
    ExecutionVariablesResolver,
)
from test_service.domain.model.exceptions.secret_resolution_exception import (
    SecretResolutionException,
)
from test_service.domain.model.execution.environment import SecretReference


class TestExecutionVariablesResolver:
    @pytest.fixture
    def secret_resolver(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def resolver(self, secret_resolver: AsyncMock) -> ExecutionVariablesResolver:
        return ExecutionVariablesResolver(secret_resolver)

    async def test_when_configuration_has_scalars_expect_text_variables(self, resolver) -> None:
        configuration = {
            "baseUrl": "https://api.example.test",
            "retries": 3,
            "ratio": 0.5,
            "debug": True,
            "quiet": False,
        }

        variables = await resolver.resolve(configuration)

        assert variables.values == {
            "baseUrl": "https://api.example.test",
            "retries": "3",
            "ratio": "0.5",
            "debug": "true",
            "quiet": "false",
        }
        assert variables.secrets == frozenset()

    @pytest.mark.parametrize("configuration", [None, {}], ids=["missing", "empty"])
    async def test_when_configuration_is_empty_expect_no_variables(
        self, resolver, secret_resolver, configuration
    ) -> None:
        variables = await resolver.resolve(configuration)

        assert variables.values == {}
        assert variables.secrets == frozenset()
        secret_resolver.resolve.assert_not_awaited()

    async def test_when_configuration_has_secret_reference_expect_resolved_value_and_tracked_secret(
        self, resolver, secret_resolver
    ) -> None:
        reference = SecretReference("env", "API_KEY")
        secret_resolver.resolve.return_value = "resolved-secret"

        variables = await resolver.resolve({"apiKey": reference, "baseUrl": "https://api.test"})

        assert variables.values == {"apiKey": "resolved-secret", "baseUrl": "https://api.test"}
        assert variables.secrets == frozenset({"resolved-secret"})
        secret_resolver.resolve.assert_awaited_once_with(reference)

    async def test_when_value_is_not_scalar_expect_it_not_exposed_as_variable(
        self, resolver
    ) -> None:
        configuration = {"nested": {"a": 1}, "items": [1, 2], "empty": None, "name": "kept"}

        variables = await resolver.resolve(configuration)

        assert variables.values == {"name": "kept"}

    async def test_when_secret_cannot_be_resolved_expect_exception_propagated(
        self, resolver, secret_resolver
    ) -> None:
        secret_resolver.resolve.side_effect = SecretResolutionException("secret is not available")

        with pytest.raises(SecretResolutionException) as exc:
            await resolver.resolve({"apiKey": SecretReference("env", "MISSING")})

        assert exc.value.code == "SECRET_RESOLUTION_FAILED"

    async def test_when_resolved_expect_values_are_read_only(self, resolver) -> None:
        variables = await resolver.resolve({"baseUrl": "https://api.test"})

        assert isinstance(variables.values, MappingProxyType)
        with pytest.raises(TypeError):
            variables.values["baseUrl"] = "changed"
