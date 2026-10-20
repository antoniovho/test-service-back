import json
from base64 import urlsafe_b64encode
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
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
            entity_version=1,
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

    @pytest.mark.parametrize(
        ("entity_type", "mutation", "entity", "expected_variable"),
        (
            (ViewerEntityType.PRECONDITION, "createPrecondition", "precondition", "definition"),
            (ViewerEntityType.TEST_SET, "createTestSet", "testSet", "testIssueIds"),
            (ViewerEntityType.TEST_PLAN, "createTestPlan", "testPlan", "testIssueIds"),
        ),
    )
    async def test_when_creating_supported_entity_expect_matching_xray_mutation(
        self,
        settings: XraySettings,
        projection: ViewerProjection,
        entity_type: ViewerEntityType,
        mutation: str,
        entity: str,
        expected_variable: str,
    ) -> None:
        requests: list[httpx.Request] = []
        entity_projection = replace(
            projection,
            record=replace(projection.record, entity_type=entity_type),
            test_external_ids=("10001",),
        )

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(
                200,
                json={
                    "data": {mutation: {entity: {"issueId": "10002", "jira": {"key": "SHOP-12"}}}}
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            identity = await XrayViewerAdapter(settings, client).publish(entity_projection)

        graphql_body = json.loads(requests[1].content)
        assert identity.external_id == "10002"
        assert mutation in graphql_body["query"]
        assert expected_variable in graphql_body["variables"]

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

    async def test_when_xray_rejects_a_cached_token_expect_reauthentication(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        authentication_requests = 0
        graphql_requests = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal authentication_requests, graphql_requests
            if request.url.path == "/auth":
                authentication_requests += 1
                return httpx.Response(200, json=f"xray-token-{authentication_requests}")
            graphql_requests += 1
            if graphql_requests == 1:
                return httpx.Response(401)
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

        assert identity.external_key == "SHOP-12"
        assert authentication_requests == 2
        assert graphql_requests == 2

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

    async def test_when_external_identity_is_missing_expect_missing_drift(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        observation = await XrayViewerAdapter(settings).check_drift(projection)

        assert observation is not None
        assert observation.drift_type is DriftType.MISSING
        assert observation.details == {"reason": "missing external identity"}

    async def test_when_xray_returns_invalid_remote_steps_expect_protocol_error(
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
                json={"data": {"getTests": {"results": [{"issueId": "10002", "steps": {}}]}}},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)

            with pytest.raises(XrayProtocolError, match="does not contain steps"):
                await adapter.check_drift(published_projection)

    async def test_when_xray_returns_non_transient_http_error_expect_transport_error(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/auth":
                return httpx.Response(200, json="xray-token")
            return httpx.Response(422)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = XrayViewerAdapter(settings, client)

            with pytest.raises(XrayTransportError, match="request failed"):
                await adapter.publish(projection)

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

    @pytest.mark.parametrize(
        ("payload", "message"),
        (
            ({}, "createTest response does not contain an entity"),
            ({"createTest": {}}, "createTest response does not contain an entity"),
            (
                {"createTest": {"test": {"jira": {"key": "SHOP-12"}}}},
                "createTest response does not contain an issueId",
            ),
            (
                {"createTest": {"test": {"issueId": "10002"}}},
                "createTest response does not contain a Jira key",
            ),
        ),
    )
    def test_when_create_response_has_invalid_identity_expect_protocol_error(
        self, payload: dict[str, object], message: str
    ) -> None:
        mutation = "createTest"
        entity = "test"

        with pytest.raises(XrayProtocolError, match=message):
            XrayViewerAdapter._identity(payload, mutation, entity)

    @pytest.mark.parametrize("payload", ({}, {"getTests": {}}))
    def test_when_read_response_has_invalid_results_expect_protocol_error(
        self, payload: dict[str, object]
    ) -> None:
        entity_type = ViewerEntityType.TEST_CASE

        with pytest.raises(XrayProtocolError, match="getTests response does not contain results"):
            XrayViewerAdapter._results(payload, entity_type)

    @pytest.mark.parametrize(
        ("payload", "message"),
        (
            ([], "GraphQL response must be an object"),
            ({"data": []}, "GraphQL response does not contain data"),
        ),
    )
    def test_when_graphql_payload_is_invalid_expect_protocol_error(
        self, payload: object, message: str
    ) -> None:
        request = httpx.Request("POST", "https://xray.example.test/graphql")
        response = httpx.Response(200, json=payload, request=request)

        with pytest.raises(XrayProtocolError, match=message):
            XrayViewerAdapter._graphql_data(response)

    def test_when_step_response_has_invalid_fields_expect_protocol_error(self) -> None:
        step = {"action": "submit", "data": 1, "result": None}

        with pytest.raises(XrayProtocolError, match="test step has invalid fields"):
            XrayViewerAdapter._step_from_response(step)

    def test_when_relationship_contains_invalid_issue_id_expect_protocol_error(self) -> None:
        results = [{"issueId": None}]

        with pytest.raises(XrayProtocolError, match="tests response contains an invalid issueId"):
            XrayViewerAdapter._issue_ids(results, "tests")

    @pytest.mark.parametrize(
        ("result", "message"),
        (
            ({}, "response does not contain tests"),
            ({"tests": {"results": [], "total": "one"}}, "paginated tests"),
        ),
    )
    async def test_when_relationship_response_is_invalid_expect_protocol_error(
        self, settings: XraySettings, result: dict[str, object], message: str
    ) -> None:
        adapter = XrayViewerAdapter(settings)
        entity_type = ViewerEntityType.TEST_SET

        with pytest.raises(XrayProtocolError, match=message):
            await adapter._relationship_issue_ids(entity_type, "10002", "tests", result)

    async def test_when_precondition_has_no_definition_expect_protocol_error(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        precondition_projection = replace(
            projection,
            record=replace(
                projection.record,
                entity_type=ViewerEntityType.PRECONDITION,
                external_entity_id="10002",
            ),
        )
        adapter = XrayViewerAdapter(settings)
        result: dict[str, object] = {}

        with pytest.raises(
            XrayProtocolError, match="precondition response does not contain a definition"
        ):
            await adapter._remote_state(precondition_projection, result)

    async def test_when_remote_state_lacks_identity_expect_protocol_error(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        adapter = XrayViewerAdapter(settings)
        result: dict[str, object] = {}

        with pytest.raises(XrayProtocolError, match="read requires an external identity"):
            await adapter._remote_state(projection, result)

    def test_when_token_contains_numeric_expiration_expect_decoded_expiry(self) -> None:
        encoded_payload = urlsafe_b64encode(b'{"exp": 1800000000}').decode().rstrip("=")
        token = f"header.{encoded_payload}.signature"

        expires_at = XrayViewerAdapter._token_expiration(token)

        assert expires_at == datetime(2027, 1, 15, 7, 59, tzinfo=UTC)

    async def test_when_precondition_exists_expect_definition_updated(
        self, monkeypatch, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        precondition_projection = replace(
            projection,
            record=replace(
                projection.record,
                entity_type=ViewerEntityType.PRECONDITION,
                external_entity_id="10002",
            ),
            description="The customer is authenticated.",
        )
        adapter = XrayViewerAdapter(settings)
        graphql = AsyncMock()
        monkeypatch.setattr(adapter, "_graphql", graphql)

        await adapter._update_projection(precondition_projection)

        graphql.assert_awaited_once_with(
            adapter._UPDATE_PRECONDITION,
            {"issueId": "10002", "definition": "The customer is authenticated."},
        )

    async def test_when_test_set_has_missing_tests_expect_xray_addition(
        self, monkeypatch, settings: XraySettings
    ) -> None:
        adapter = XrayViewerAdapter(settings)
        relationship_issue_ids = AsyncMock(return_value=())
        graphql = AsyncMock()
        monkeypatch.setattr(adapter, "_relationship_issue_ids", relationship_issue_ids)
        monkeypatch.setattr(adapter, "_graphql", graphql)

        await adapter._remove_stale_tests(ViewerEntityType.TEST_SET, "10002", ("10003",))

        graphql.assert_awaited_once_with(
            adapter._ADD_TESTS_TO_SET,
            {"issueId": "10002", "testIssueIds": ["10003"]},
        )

    def test_when_xray_rejects_token_expect_authentication_error_and_token_cleared(
        self, settings: XraySettings
    ) -> None:
        request = httpx.Request("POST", settings.graphql_url)
        response = httpx.Response(401, request=request)
        adapter = XrayViewerAdapter(settings)
        adapter._access_token = "expired-token"
        adapter._access_token_expires_at = datetime(2026, 1, 1, tzinfo=UTC)

        error = adapter._retry_error(response)

        assert isinstance(error, XrayAuthenticationError)
        assert adapter._access_token is None
        assert adapter._access_token_expires_at is None

    async def test_when_request_times_out_on_last_attempt_expect_transport_error(
        self, monkeypatch, settings: XraySettings
    ) -> None:
        adapter = XrayViewerAdapter(settings.model_copy(update={"max_attempts": 1}))
        graphql_once = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        monkeypatch.setattr(adapter, "_graphql_once", graphql_once)

        with pytest.raises(XrayTransportError, match="request failed after retries"):
            await adapter._graphql("query", {})

    async def test_when_access_token_is_still_valid_expect_cached_token(
        self, settings: XraySettings
    ) -> None:
        adapter = XrayViewerAdapter(settings)
        client = AsyncMock()
        adapter._access_token = "cached-token"
        adapter._access_token_expires_at = datetime.now(UTC) + timedelta(minutes=1)

        token = await adapter._authenticate(client)

        assert token == "cached-token"
        client.post.assert_not_awaited()

    def test_when_token_expiration_is_invalid_expect_fallback_expiry(self) -> None:
        before = datetime.now(UTC)

        expires_at = XrayViewerAdapter._token_expiration("not-a-jwt")

        assert before + timedelta(hours=22) < expires_at <= before + timedelta(hours=24)

    def test_when_json_response_is_invalid_expect_protocol_error(self) -> None:
        response = httpx.Response(200, content=b"invalid json")

        with pytest.raises(XrayProtocolError, match="GraphQL response is not valid JSON"):
            XrayViewerAdapter._json_payload(response, "GraphQL")

    async def test_when_timeout_is_transient_expect_request_retry(
        self, monkeypatch, settings: XraySettings
    ) -> None:
        request = httpx.Request("POST", settings.graphql_url)
        successful_response = httpx.Response(200, json={"data": {}}, request=request)
        adapter = XrayViewerAdapter(settings.model_copy(update={"max_attempts": 2}))
        graphql_once = AsyncMock(
            side_effect=(httpx.TimeoutException("timeout"), successful_response)
        )
        monkeypatch.setattr(adapter, "_graphql_once", graphql_once)

        data = await adapter._graphql("query", {})

        assert data == {}
        assert graphql_once.await_count == 2

    async def test_when_authentication_request_fails_expect_authentication_error(
        self, settings: XraySettings
    ) -> None:
        request = httpx.Request("POST", settings.auth_url)
        response = httpx.Response(401, request=request)
        client = AsyncMock()
        client.post.return_value = response
        adapter = XrayViewerAdapter(settings)

        with pytest.raises(XrayAuthenticationError, match="authentication request failed"):
            await adapter._authenticate(client)

    async def test_when_relationship_query_returns_no_entity_expect_protocol_error(
        self, monkeypatch, settings: XraySettings
    ) -> None:
        adapter = XrayViewerAdapter(settings)
        graphql = AsyncMock(return_value={"getTestSets": {"results": []}})
        monkeypatch.setattr(adapter, "_graphql", graphql)

        with pytest.raises(
            XrayProtocolError, match="relationship response does not contain an entity"
        ):
            await adapter._relationship_issue_ids(ViewerEntityType.TEST_SET, "10002", "tests")

    async def test_when_remote_result_is_not_an_object_expect_protocol_error(
        self, settings: XraySettings, projection: ViewerProjection
    ) -> None:
        adapter = XrayViewerAdapter(settings)
        result: object = []

        with pytest.raises(XrayProtocolError, match="query result must be an object"):
            await adapter._remote_state(projection, result)
