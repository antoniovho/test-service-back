from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import SecretStr

from test_service.config import JiraSettings
from test_service.domain.model.exceptions.external_project_not_found_exception import (
    ExternalProjectNotFoundException,
    ExternalProjectProviderException,
)
from test_service.infrastructure.adapters.output.projects.jira import (
    jira_project_validation_adapter,
)
from test_service.infrastructure.adapters.output.projects.jira.jira_project_validation_adapter import (  # noqa: E501
    JiraProjectValidationAdapter,
)


class _ManagedClient:
    def __init__(self, client) -> None:
        self._client = client

    async def __aenter__(self):
        return self._client

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        return None


@pytest.fixture
def settings() -> JiraSettings:
    return JiraSettings(
        base_url="https://jira.example.test/",
        user_email="user@example.test",
        api_token=SecretStr("api-token"),
    )


class TestJiraProjectValidationAdapter:
    async def test_when_project_exists_expect_validated_project(
        self, settings: JiraSettings
    ) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await JiraProjectValidationAdapter(settings, client).validate("SHOP")

        assert requests[0].url == "https://jira.example.test/rest/api/3/project/SHOP"
        assert requests[0].headers["Accept"] == "application/json"
        assert requests[0].headers["Authorization"].startswith("Basic ")

    @pytest.mark.parametrize("status", [httpx.codes.NOT_FOUND, httpx.codes.FORBIDDEN])
    async def test_when_project_is_not_accessible_expect_not_found_error(
        self, settings: JiraSettings, status: int
    ) -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(status))
        ) as client:
            adapter = JiraProjectValidationAdapter(settings, client)

            with pytest.raises(ExternalProjectNotFoundException):
                await adapter.validate("SHOP")

    async def test_when_jira_returns_provider_error_expect_provider_exception(
        self, settings: JiraSettings
    ) -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(500))
        ) as client:
            adapter = JiraProjectValidationAdapter(settings, client)

            with pytest.raises(ExternalProjectProviderException):
                await adapter.validate("SHOP")

    async def test_when_jira_transport_fails_expect_provider_exception(
        self, settings: JiraSettings
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("unavailable", request=request)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = JiraProjectValidationAdapter(settings, client)

            with pytest.raises(ExternalProjectProviderException):
                await adapter.validate("SHOP")

    async def test_when_client_is_not_injected_expect_managed_client_request(
        self, settings: JiraSettings, monkeypatch
    ) -> None:
        client = type("Client", (), {"get": AsyncMock(return_value=httpx.Response(200))})()
        monkeypatch.setattr(
            jira_project_validation_adapter.httpx,
            "AsyncClient",
            lambda timeout: _ManagedClient(client),
        )

        await JiraProjectValidationAdapter(settings).validate("SHOP")

        client.get.assert_awaited_once()
