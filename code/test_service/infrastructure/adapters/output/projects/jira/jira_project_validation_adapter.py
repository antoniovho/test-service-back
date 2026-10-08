"""Jira implementation of the provider-neutral ProjectValidationPort."""
# ruff: noqa: E501

import base64

import httpx

from test_service.config import JiraSettings
from test_service.domain.model.exceptions.external_project_not_found_exception import (
    ExternalProjectNotFoundException,
    ExternalProjectProviderException,
)
from test_service.domain.ports.output.projects.project_validation_port import ProjectValidationPort


class JiraProjectValidationAdapter(ProjectValidationPort):
    """Use Jira's project endpoint without leaking Jira into the application layer."""

    def __init__(self, settings: JiraSettings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    async def validate(self, project_key: str) -> None:
        try:
            if self._client is not None:
                response = await self._client.get(
                    self._project_url(project_key), headers=self._headers()
                )
            else:
                async with httpx.AsyncClient(timeout=self._settings.timeout_seconds) as client:
                    response = await client.get(
                        self._project_url(project_key), headers=self._headers()
                    )
        except httpx.HTTPError as exc:
            raise ExternalProjectProviderException() from exc
        if response.status_code in {httpx.codes.NOT_FOUND, httpx.codes.FORBIDDEN}:
            raise ExternalProjectNotFoundException(project_key)
        if response.is_error:
            raise ExternalProjectProviderException()

    def _project_url(self, project_key: str) -> str:
        return f"{self._settings.base_url.rstrip('/')}/rest/api/3/project/{project_key}"

    def _headers(self) -> dict[str, str]:
        credentials = f"{self._settings.user_email}:{self._settings.api_token.get_secret_value()}"
        token = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {token}", "Accept": "application/json"}
