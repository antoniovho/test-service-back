import json
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from test_service.config import XraySettings
from test_service.domain.model.viewer.records import (
    DriftType,
    SyncStatus,
    ViewerEntityType,
    ViewerSyncRecord,
    ViewerType,
)
from test_service.infrastructure.adapters.output.viewer.xray_exceptions import (
    XrayAuthenticationError,
    XrayProtocolError,
    XrayTransportError,
)
from test_service.infrastructure.adapters.output.viewer.xray_viewer_adapter import (
    XrayViewerAdapter,
)


class TestXrayViewerAdapter:
    @pytest.fixture
    def settings(self) -> XraySettings:
        return XraySettings(
            client_id="client-id",
            client_secret=SecretStr("client-secret"),
            auth_url="https://xray.example.test/auth",
            projection_url="https://xray.example.test/projections",
            drift_check_url="https://xray.example.test/drift",
        )

    @pytest.fixture
    def record(self) -> ViewerSyncRecord:
        return ViewerSyncRecord(
            identifier=uuid4(),
            project_key="SHOP",
            entity_type=ViewerEntityType.TEST_CASE,
            entity_key="checkout",
            projected_version_id=uuid4(),
            viewer_type=ViewerType.XRAY,
            external_entity_key="SHOP-123",
            sync_status=SyncStatus.PENDING,
            created_at=datetime.now(UTC),
        )

    async def test_when_publishing_expect_authenticated_projection_request(
        self, settings: XraySettings, record: ViewerSyncRecord
    ) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(202)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)

            await adapter.publish(record)

        assert len(requests) == 2
        assert json.loads(requests[0].content) == {
            "client_id": "client-id",
            "client_secret": "client-secret",
        }
        assert requests[1].headers["Authorization"] == "Bearer xray-token"
        assert json.loads(requests[1].content)["projectedVersionId"] == str(
            record.projected_version_id
        )
        assert "client-secret" not in requests[1].content.decode()

    async def test_when_checking_drift_expect_configured_endpoint_is_called(
        self, settings: XraySettings, record: ViewerSyncRecord
    ) -> None:
        paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            paths.append(request.url.path)
            if request.url.path == "/auth":
                return httpx.Response(200, json={"token": "xray-token"})
            return httpx.Response(204)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)

            observation = await adapter.check_drift(record)

        assert paths == ["/auth", "/drift"]
        assert observation is None

    async def test_when_drift_response_contains_safe_observation_expect_normalized_result(
        self, settings: XraySettings, record: ViewerSyncRecord
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(
                200,
                json={"driftType": "MODIFIED", "details": {"field": "summary"}},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            observation = await XrayViewerAdapter(settings, client).check_drift(record)

        assert observation is not None
        assert observation.drift_type is DriftType.MODIFIED
        assert observation.details == {"field": "summary"}

    async def test_when_authentication_response_has_no_token_expect_provider_error(
        self, settings: XraySettings, record: ViewerSyncRecord
    ) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)

            with pytest.raises(XrayAuthenticationError, match="does not contain a token"):
                await adapter.publish(record)

    async def test_when_drift_response_is_invalid_expect_protocol_error(
        self, settings: XraySettings, record: ViewerSyncRecord
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(200, json={"details": {}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)

            with pytest.raises(XrayProtocolError, match="does not contain a driftType"):
                await adapter.check_drift(record)

    async def test_when_xray_returns_unsuccessful_status_expect_transport_error(
        self, settings: XraySettings, record: ViewerSyncRecord
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(503, request=request)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)

            with pytest.raises(XrayTransportError, match="Xray request failed"):
                await adapter.publish(record)

    async def test_when_no_attempts_are_configured_expect_transport_error(
        self, settings: XraySettings, record: ViewerSyncRecord
    ) -> None:
        adapter = XrayViewerAdapter(settings.model_copy(update={"max_attempts": 0}))

        with pytest.raises(XrayTransportError, match="no configured attempts"):
            await adapter.publish(record)
