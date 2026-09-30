import json
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from test_service.config import XraySettings
from test_service.domain.model.viewer.records import (
    SyncStatus,
    ViewerEntityType,
    ViewerSyncRecord,
    ViewerType,
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

            await adapter.check_drift(record)

        assert paths == ["/auth", "/drift"]

    async def test_when_authentication_response_has_no_token_expect_value_error(
        self, settings: XraySettings, record: ViewerSyncRecord
    ) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)

            with pytest.raises(ValueError, match="does not contain a token"):
                await adapter.publish(record)
