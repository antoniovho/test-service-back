import json
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from test_service.config import XraySettings
from test_service.domain.model.viewer.projection import ViewerProjection, ViewerProjectionStep
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
            graphql_url="https://xray.example.test/graphql",
            rate_limit_requests=10_000,
            rate_limit_window_seconds=1,
            retry_backoff_seconds=0,
        )

    @pytest.fixture
    def projection(self) -> ViewerProjection:
        record = ViewerSyncRecord(
            identifier=uuid4(),
            project_key="SHOP",
            entity_type=ViewerEntityType.TEST_CASE,
            entity_key="checkout",
            projected_version_id=uuid4(),
            viewer_type=ViewerType.XRAY,
            external_entity_key="checkout",
            sync_status=SyncStatus.PENDING,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        return ViewerProjection(
            record=record,
            summary="Checkout succeeds",
            description="A customer can complete checkout.",
            steps=(ViewerProjectionStep("submit: http", '{"method":"POST"}', "201 Created"),),
            precondition_external_ids=("10001",),
        )

    async def test_when_creating_test_expect_authenticated_graphql_projection_and_identity(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(
                200,
                json={
                    "data": {
                        "createTest": {"test": {"issueId": "10002", "jira": {"key": "SHOP-12"}}}
                    }
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            identity = await XrayViewerAdapter(settings, client).publish(projection)

        graphql_body = json.loads(requests[1].content)
        assert identity.external_id == "10002"
        assert identity.external_key == "SHOP-12"
        assert json.loads(requests[0].content) == {
            "client_id": "client-id",
            "client_secret": "client-secret",
        }
        assert requests[1].headers["Authorization"] == "Bearer xray-token"
        assert graphql_body["variables"]["testType"] == {"name": "Manual"}
        assert graphql_body["variables"]["preconditionIssueIds"] == ["10001"]
        assert graphql_body["variables"]["steps"][0]["action"] == "submit: http"
        assert "client-secret" not in requests[1].content.decode()

    async def test_when_publishing_twice_expect_cached_token_and_update(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        requests: list[httpx.Request] = []
        updated_projection = ViewerProjection(
            record=replace(
                projection.record, external_entity_id="10002", external_entity_key="SHOP-12"
            ),
            summary=projection.summary,
            steps=projection.steps,
        )

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            body = json.loads(request.content)
            if "createTest" in body["query"]:
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "createTest": {"test": {"issueId": "10002", "jira": {"key": "SHOP-12"}}}
                        }
                    },
                )
            if "getTests" in body["query"]:
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "getTests": {
                                "results": [
                                    {
                                        "issueId": "10002",
                                        "steps": [],
                                        "preconditions": {"total": 0, "results": []},
                                    }
                                ]
                            }
                        }
                    },
                )
            return httpx.Response(200, json={"data": {"updateTestType": {}}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)
            await adapter.publish(projection)
            identity = await adapter.publish(updated_projection)

        assert identity.external_id == "10002"
        assert sum(request.url.path == "/auth" for request in requests) == 1
        assert any("removeAllTestSteps" in request.content.decode() for request in requests)
        assert any("addTestStep" in request.content.decode() for request in requests)

    @pytest.mark.parametrize(
        ("entity_type", "query_name", "remove_mutation"),
        (
            (ViewerEntityType.TEST_SET, "getTestSets", "removeTestsFromTestSet"),
            (ViewerEntityType.TEST_PLAN, "getTestPlans", "removeTestsFromTestPlan"),
        ),
    )
    async def test_when_set_or_plan_has_stale_tests_expect_xray_removal(
        self,
        settings: XraySettings,
        projection: ViewerProjection,
        entity_type: ViewerEntityType,
        query_name: str,
        remove_mutation: str,
    ) -> None:
        updated_projection = ViewerProjection(
            record=replace(
                projection.record,
                entity_type=entity_type,
                external_entity_id="10002",
                external_entity_key="SHOP-12",
            ),
            summary=projection.summary,
        )
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            body = json.loads(request.content)
            if query_name in body["query"]:
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            query_name: {
                                "results": [
                                    {
                                        "issueId": "10002",
                                        "tests": {"total": 1, "results": [{"issueId": "10001"}]},
                                    }
                                ]
                            }
                        }
                    },
                )
            return httpx.Response(200, json={"data": {remove_mutation: {"warnings": []}}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await XrayViewerAdapter(settings, client).publish(updated_projection)

        assert any(remove_mutation in request.content.decode() for request in requests)

    async def test_when_xray_returns_transient_status_expect_request_is_retried(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        graphql_attempts = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal graphql_attempts
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            graphql_attempts += 1
            if graphql_attempts == 1:
                return httpx.Response(503)
            return httpx.Response(
                200,
                json={
                    "data": {
                        "createTest": {"test": {"issueId": "10002", "jira": {"key": "SHOP-12"}}}
                    }
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            identity = await XrayViewerAdapter(settings, client).publish(projection)

        assert identity.external_id == "10002"
        assert graphql_attempts == 2

    async def test_when_graphql_returns_errors_expect_protocol_error(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(200, json={"errors": [{"message": "invalid field"}]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)

            with pytest.raises(XrayProtocolError, match="contains errors"):
                await adapter.publish(projection)

    async def test_when_authentication_has_no_token_expect_authentication_error(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)

            with pytest.raises(XrayAuthenticationError, match="does not contain a token"):
                await adapter.publish(projection)

    async def test_when_xray_keeps_failing_expect_transport_error(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(503)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)

            with pytest.raises(XrayTransportError, match="after retries"):
                await adapter.publish(projection)

    async def test_when_remote_entity_is_absent_expect_deleted_drift(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        record = replace(
            projection.record, external_entity_id="10002", external_entity_key="SHOP-12"
        )

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(200, json={"data": {"getTests": {"results": []}}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            observation = await XrayViewerAdapter(settings, client).check_drift(
                ViewerProjection(record=record, summary="Checkout succeeds")
            )

        assert observation is not None
        assert observation.drift_type is DriftType.DELETED

    async def test_when_remote_managed_state_matches_expect_no_drift(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        published_projection = replace(
            projection,
            record=replace(
                projection.record, external_entity_id="10002", external_entity_key="SHOP-12"
            ),
        )

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(
                200,
                json={
                    "data": {
                        "getTests": {
                            "results": [
                                {
                                    "issueId": "10002",
                                    "steps": [
                                        {
                                            "action": "submit: http",
                                            "data": '{"method":"POST"}',
                                            "result": "201 Created",
                                        }
                                    ],
                                    "preconditions": {
                                        "total": 1,
                                        "results": [{"issueId": "10001"}],
                                    },
                                }
                            ]
                        }
                    }
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            observation = await XrayViewerAdapter(settings, client).check_drift(
                published_projection
            )

        assert observation is None

    async def test_when_remote_step_differs_expect_safe_modified_observation(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        published_projection = replace(
            projection,
            record=replace(
                projection.record, external_entity_id="10002", external_entity_key="SHOP-12"
            ),
        )

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(
                200,
                json={
                    "data": {
                        "getTests": {
                            "results": [
                                {
                                    "issueId": "10002",
                                    "steps": [
                                        {
                                            "action": "remote secret action",
                                            "data": None,
                                            "result": None,
                                        }
                                    ],
                                    "preconditions": {
                                        "total": 1,
                                        "results": [{"issueId": "10001"}],
                                    },
                                }
                            ]
                        }
                    }
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            observation = await XrayViewerAdapter(settings, client).check_drift(
                published_projection
            )

        assert observation is not None
        assert observation.drift_type is DriftType.MODIFIED
        assert observation.details == {"fields": ("steps",)}
        assert "remote secret action" not in str(observation.details)

    async def test_when_preconditions_are_paginated_expect_no_drift(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        precondition_external_ids = tuple(str(issue_id) for issue_id in range(1, 102))
        published_projection = replace(
            projection,
            record=replace(
                projection.record, external_entity_id="10002", external_entity_key="SHOP-12"
            ),
            precondition_external_ids=precondition_external_ids,
        )
        relationship_starts: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            variables = json.loads(request.content)["variables"]
            relationship_start = variables["relationshipStart"]
            relationship_starts.append(relationship_start)
            issue_ids = precondition_external_ids[relationship_start : relationship_start + 100]
            return httpx.Response(
                200,
                json={
                    "data": {
                        "getTests": {
                            "results": [
                                {
                                    "issueId": "10002",
                                    "steps": [
                                        {
                                            "action": "submit: http",
                                            "data": '{"method":"POST"}',
                                            "result": "201 Created",
                                        }
                                    ],
                                    "preconditions": {
                                        "total": len(precondition_external_ids),
                                        "results": [
                                            {"issueId": issue_id} for issue_id in issue_ids
                                        ],
                                    },
                                }
                            ]
                        }
                    }
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            observation = await XrayViewerAdapter(settings, client).check_drift(
                published_projection
            )

        assert observation is None
        assert relationship_starts == [0, 100]
