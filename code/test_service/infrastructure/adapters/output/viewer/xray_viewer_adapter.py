"""Xray Cloud adapter for Viewer projection and drift operations."""

import asyncio
import json
from collections.abc import Mapping

import httpx

from test_service.config import XraySettings
from test_service.domain.model.viewer.records import DriftObservation, DriftType, ViewerSyncRecord
from test_service.domain.ports.output.viewer.viewer_drift_detector_port import (
    ViewerDriftDetectorPort,
)
from test_service.domain.ports.output.viewer.viewer_publisher_port import ViewerPublisherPort
from test_service.infrastructure.adapters.output.viewer.xray_exceptions import (
    XrayAuthenticationError,
    XrayProtocolError,
    XrayTransportError,
)


class XrayViewerAdapter(ViewerPublisherPort, ViewerDriftDetectorPort):
    """Publish canonical Viewer metadata through authenticated Xray HTTP endpoints."""

    def __init__(self, settings: XraySettings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    async def publish(self, record: ViewerSyncRecord) -> None:
        """Send an idempotent projection request to the configured Xray endpoint."""
        await self._request("POST", self._settings.projection_url, record)

    async def check_drift(self, record: ViewerSyncRecord) -> DriftObservation | None:
        """Return the normalized drift result for one published projection."""
        response = await self._request("POST", self._settings.drift_check_url, record)
        if not response.content:
            return None
        payload = self._json_payload(response, "drift")
        if payload is None:
            return None
        if not isinstance(payload, Mapping):
            raise XrayProtocolError("Xray drift response does not contain a driftType")
        drift_type_value = payload.get("driftType")
        if not isinstance(drift_type_value, str):
            raise XrayProtocolError("Xray drift response does not contain a driftType")
        details = payload.get("details")
        if details is not None and not isinstance(details, Mapping):
            raise XrayProtocolError("Xray drift response details must be an object")
        try:
            drift_type = DriftType(drift_type_value)
        except ValueError as exc:
            raise XrayProtocolError("Xray drift response has an unsupported driftType") from exc
        return DriftObservation(drift_type, details)

    async def _request(self, method: str, url: str, record: ViewerSyncRecord) -> httpx.Response:
        """Perform bounded retries only for transient transport/provider failures."""
        for attempt in range(1, self._settings.max_attempts + 1):
            try:
                return await self._request_once(method, url, record)
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
                if attempt == self._settings.max_attempts:
                    raise XrayTransportError("Xray request failed after retries") from exc
                await asyncio.sleep(self._settings.retry_backoff_seconds * (2 ** (attempt - 1)))
            except httpx.HTTPError as exc:
                raise XrayTransportError("Xray request failed") from exc
        raise XrayTransportError("Xray request has no configured attempts")

    async def _request_once(
        self, method: str, url: str, record: ViewerSyncRecord
    ) -> httpx.Response:
        if self._client is not None:
            return await self._send(self._client, method, url, record)
        timeout = httpx.Timeout(self._settings.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await self._send(client, method, url, record)

    async def _send(
        self, client: httpx.AsyncClient, method: str, url: str, record: ViewerSyncRecord
    ) -> httpx.Response:
        token = await self._authenticate(client)
        response = await client.request(
            method,
            url,
            headers={"Authorization": f"Bearer {token}"},
            json=self._record_payload(record),
        )
        response.raise_for_status()
        return response

    async def _authenticate(self, client: httpx.AsyncClient) -> str:
        response = await client.post(
            self._settings.auth_url,
            json={
                "client_id": self._settings.client_id,
                "client_secret": self._settings.client_secret.get_secret_value(),
            },
        )
        response.raise_for_status()
        payload = self._json_payload(response, "authentication")
        if isinstance(payload, str) and payload:
            return payload
        if isinstance(payload, Mapping) and isinstance(payload.get("token"), str):
            return payload["token"]
        raise XrayAuthenticationError("Xray authentication response does not contain a token")

    @staticmethod
    def _json_payload(response: httpx.Response, operation: str) -> object:
        """Return a JSON response body or normalize a malformed payload error."""
        try:
            return response.json()
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise XrayProtocolError(f"Xray {operation} response is not valid JSON") from exc

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
