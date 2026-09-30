"""Xray Cloud adapter for Viewer projection and drift operations."""

from collections.abc import Mapping

import httpx

from test_service.config import XraySettings
from test_service.domain.model.viewer.records import ViewerSyncRecord
from test_service.domain.ports.output.viewer.viewer_drift_detector_port import (
    ViewerDriftDetectorPort,
)
from test_service.domain.ports.output.viewer.viewer_publisher_port import ViewerPublisherPort


class XrayViewerAdapter(ViewerPublisherPort, ViewerDriftDetectorPort):
    """Publish canonical Viewer metadata through authenticated Xray HTTP endpoints."""

    def __init__(self, settings: XraySettings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    async def publish(self, record: ViewerSyncRecord) -> None:
        """Send an idempotent projection request to the configured Xray endpoint."""
        await self._request("POST", self._settings.projection_url, record)

    async def check_drift(self, record: ViewerSyncRecord) -> None:
        """Request drift validation for one previously published Xray projection."""
        await self._request("POST", self._settings.drift_check_url, record)

    async def _request(self, method: str, url: str, record: ViewerSyncRecord) -> None:
        if self._client is not None:
            await self._send(self._client, method, url, record)
            return
        timeout = httpx.Timeout(self._settings.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            await self._send(client, method, url, record)

    async def _send(
        self, client: httpx.AsyncClient, method: str, url: str, record: ViewerSyncRecord
    ) -> None:
        token = await self._authenticate(client)
        response = await client.request(
            method,
            url,
            headers={"Authorization": f"Bearer {token}"},
            json=self._record_payload(record),
        )
        response.raise_for_status()

    async def _authenticate(self, client: httpx.AsyncClient) -> str:
        response = await client.post(
            self._settings.auth_url,
            json={
                "client_id": self._settings.client_id,
                "client_secret": self._settings.client_secret.get_secret_value(),
            },
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, str) and payload:
            return payload
        if isinstance(payload, Mapping) and isinstance(payload.get("token"), str):
            return payload["token"]
        raise ValueError("Xray authentication response does not contain a token")

    @staticmethod
    def _record_payload(record: ViewerSyncRecord) -> dict[str, str | None]:
        return {
            "projectKey": record.project_key,
            "entityType": record.entity_type.value,
            "entityKey": record.entity_key,
            "projectedVersionId": str(record.projected_version_id),
            "viewerType": record.viewer_type.value,
            "externalEntityKey": record.external_entity_key,
            "externalEntityId": record.external_entity_id,
        }
