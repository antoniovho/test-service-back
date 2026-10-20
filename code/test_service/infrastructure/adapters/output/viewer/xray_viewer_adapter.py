"""Direct Xray Cloud GraphQL adapter for Viewer projection and drift operations."""

import asyncio
import base64
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

import httpx

from test_service.config import XraySettings
from test_service.domain.model.viewer.managed_state import ViewerManagedState
from test_service.domain.model.viewer.projection import (
    ViewerExternalIdentity,
    ViewerProjection,
    ViewerProjectionStep,
)
from test_service.domain.model.viewer.records import (
    DriftObservation,
    DriftType,
    ViewerEntityType,
)
from test_service.domain.ports.output.viewer.viewer_drift_detector_port import (
    ViewerDriftDetectorPort,
)
from test_service.domain.ports.output.viewer.viewer_publisher_port import ViewerPublisherPort
from test_service.infrastructure.adapters.output.viewer.xray_exceptions import (
    XrayAuthenticationError,
    XrayAuthorizationError,
    XrayProtocolError,
    XrayProviderError,
    XrayTransportError,
    XrayValidationError,
)

_TRANSIENT_STATUS_CODES = frozenset({429, 502, 503, 504})


class XrayViewerAdapter(ViewerPublisherPort, ViewerDriftDetectorPort):
    """Publish Viewer projections through Xray Cloud's authenticated GraphQL API."""

    def __init__(self, settings: XraySettings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client
        self._access_token: str | None = None
        self._access_token_expires_at: datetime | None = None
        self._authentication_lock = asyncio.Lock()
        self._rate_limit_lock = asyncio.Lock()
        self._next_request_at = 0.0

    async def publish(self, projection: ViewerProjection) -> ViewerExternalIdentity:
        """Create or refresh the Xray entity represented by a canonical projection."""
        if projection.record.external_entity_id is not None:
            await self._update_projection(projection)
            return ViewerExternalIdentity(
                projection.record.external_entity_id, projection.record.external_entity_key
            )
        return await self._create_projection(projection)

    async def check_drift(self, projection: ViewerProjection) -> DriftObservation | None:
        """Compare provider-managed fields with the canonical published projection."""
        record = projection.record
        if record.external_entity_id is None:
            return DriftObservation(DriftType.MISSING, {"reason": "missing external identity"})
        payload = await self._graphql(
            self._read_query(record.entity_type),
            {
                "issueIds": [record.external_entity_id],
                "limit": 1,
                "relationshipLimit": 100,
                "relationshipStart": 0,
            },
        )
        results = self._results(payload, record.entity_type)
        if not results:
            return DriftObservation(DriftType.DELETED, None)
        remote_state = await self._remote_state(projection, results[0])
        differences = ViewerManagedState.from_projection(projection).differing_fields(remote_state)
        if differences:
            return DriftObservation(DriftType.MODIFIED, {"fields": differences})
        return None

    async def _create_projection(self, projection: ViewerProjection) -> ViewerExternalIdentity:
        record = projection.record
        variables: dict[str, object] = {
            "jira": self._jira_input(
                record.project_key, projection.summary, projection.description
            ),
        }
        if record.entity_type is ViewerEntityType.TEST_CASE:
            variables.update(
                {
                    "testType": {"name": "Manual"},
                    "steps": [self._step_input(step) for step in projection.steps],
                    "preconditionIssueIds": list(projection.precondition_external_ids),
                }
            )
            payload = await self._graphql(self._CREATE_TEST, variables)
            return self._identity(payload, "createTest", "test")
        if record.entity_type is ViewerEntityType.PRECONDITION:
            variables.update(
                {
                    "preconditionType": {"name": "Condition"},
                    "definition": projection.description or "",
                }
            )
            payload = await self._graphql(self._CREATE_PRECONDITION, variables)
            return self._identity(payload, "createPrecondition", "precondition")
        if record.entity_type is ViewerEntityType.TEST_SET:
            variables["testIssueIds"] = list(projection.test_external_ids)
            payload = await self._graphql(self._CREATE_TEST_SET, variables)
            return self._identity(payload, "createTestSet", "testSet")
        if record.entity_type is ViewerEntityType.TEST_PLAN:
            variables["testIssueIds"] = list(projection.test_external_ids)
            payload = await self._graphql(self._CREATE_TEST_PLAN, variables)
            return self._identity(payload, "createTestPlan", "testPlan")
        raise XrayProtocolError(f"unsupported Xray entity type: {record.entity_type}")

    async def _update_projection(self, projection: ViewerProjection) -> None:
        record = projection.record
        issue_id = record.external_entity_id
        if issue_id is None:
            raise XrayProtocolError("Xray update requires an external identity")
        if record.entity_type is ViewerEntityType.TEST_CASE:
            await self._graphql(
                self._UPDATE_TEST_TYPE, {"issueId": issue_id, "testType": {"name": "Manual"}}
            )
            await self._graphql(self._REMOVE_ALL_TEST_STEPS, {"issueId": issue_id})
            for step in projection.steps:
                await self._graphql(
                    self._ADD_TEST_STEP, {"issueId": issue_id, "step": self._step_input(step)}
                )
            current_preconditions = await self._relationship_issue_ids(
                record.entity_type, issue_id, "preconditions"
            )
            stale_preconditions = tuple(
                issue_id
                for issue_id in current_preconditions
                if issue_id not in projection.precondition_external_ids
            )
            if stale_preconditions:
                await self._graphql(
                    self._REMOVE_PRECONDITIONS,
                    {"issueId": issue_id, "preconditionIssueIds": list(stale_preconditions)},
                )
            missing_preconditions = tuple(
                precondition_external_id
                for precondition_external_id in projection.precondition_external_ids
                if precondition_external_id not in current_preconditions
            )
            if missing_preconditions:
                await self._graphql(
                    self._ADD_PRECONDITIONS,
                    {
                        "issueId": issue_id,
                        "preconditionIssueIds": list(missing_preconditions),
                    },
                )
            return
        if record.entity_type is ViewerEntityType.PRECONDITION:
            await self._graphql(
                self._UPDATE_PRECONDITION,
                {"issueId": issue_id, "definition": projection.description or ""},
            )
            return
        if record.entity_type is ViewerEntityType.TEST_SET:
            await self._remove_stale_tests(
                record.entity_type, issue_id, projection.test_external_ids
            )
            return
        if record.entity_type is ViewerEntityType.TEST_PLAN:
            await self._remove_stale_tests(
                record.entity_type, issue_id, projection.test_external_ids
            )
            return
        raise XrayProtocolError(f"unsupported Xray entity type: {record.entity_type}")

    async def _remove_stale_tests(
        self, entity_type: ViewerEntityType, issue_id: str, expected_issue_ids: tuple[str, ...]
    ) -> None:
        current_issue_ids = await self._relationship_issue_ids(entity_type, issue_id, "tests")
        stale_issue_ids = tuple(
            current_issue_id
            for current_issue_id in current_issue_ids
            if current_issue_id not in expected_issue_ids
        )
        if stale_issue_ids:
            mutation = (
                self._REMOVE_TESTS_FROM_SET
                if entity_type is ViewerEntityType.TEST_SET
                else self._REMOVE_TESTS_FROM_PLAN
            )
            await self._graphql(
                mutation, {"issueId": issue_id, "testIssueIds": list(stale_issue_ids)}
            )
        missing_issue_ids = tuple(
            expected_issue_id
            for expected_issue_id in expected_issue_ids
            if expected_issue_id not in current_issue_ids
        )
        if not missing_issue_ids:
            return
        mutation = (
            self._ADD_TESTS_TO_SET
            if entity_type is ViewerEntityType.TEST_SET
            else self._ADD_TESTS_TO_PLAN
        )
        await self._graphql(
            mutation, {"issueId": issue_id, "testIssueIds": list(missing_issue_ids)}
        )

    async def _remote_state(
        self, projection: ViewerProjection, result: object
    ) -> ViewerManagedState:
        if not isinstance(result, Mapping):
            raise XrayProtocolError("Xray query result must be an object")
        entity_type = projection.record.entity_type
        issue_id = projection.record.external_entity_id
        if issue_id is None:
            raise XrayProtocolError("Xray read requires an external identity")
        if entity_type is ViewerEntityType.TEST_CASE:
            steps = result.get("steps")
            if not isinstance(steps, list):
                raise XrayProtocolError("Xray test response does not contain steps")
            return ViewerManagedState.from_remote(
                entity_type,
                steps=tuple(self._step_from_response(step) for step in steps),
                related_external_ids=await self._relationship_issue_ids(
                    entity_type, issue_id, "preconditions", result
                ),
            )
        if entity_type is ViewerEntityType.PRECONDITION:
            definition = result.get("definition")
            if not isinstance(definition, str):
                raise XrayProtocolError("Xray precondition response does not contain a definition")
            return ViewerManagedState.from_remote(entity_type, definition=definition)
        return ViewerManagedState.from_remote(
            entity_type,
            related_external_ids=await self._relationship_issue_ids(
                entity_type, issue_id, "tests", result
            ),
        )

    async def _relationship_issue_ids(
        self,
        entity_type: ViewerEntityType,
        issue_id: str,
        field: str,
        initial_result: Mapping[str, object] | None = None,
    ) -> tuple[str, ...]:
        result = initial_result
        start = 0
        issue_ids: list[str] = []
        while True:
            if result is None:
                payload = await self._graphql(
                    self._read_query(entity_type),
                    {
                        "issueIds": [issue_id],
                        "limit": 1,
                        "relationshipLimit": 100,
                        "relationshipStart": start,
                    },
                )
                results = self._results(payload, entity_type)
                if not results or not isinstance(results[0], Mapping):
                    raise XrayProtocolError("Xray relationship response does not contain an entity")
                result = results[0]
            relationship = result.get(field)
            if not isinstance(relationship, Mapping):
                raise XrayProtocolError(f"Xray response does not contain {field}")
            related_results = relationship.get("results")
            total = relationship.get("total")
            if not isinstance(related_results, list) or not isinstance(total, int):
                raise XrayProtocolError(f"Xray response does not contain paginated {field}")
            issue_ids.extend(self._issue_ids(related_results, field))
            start += len(related_results)
            if start >= total:
                return tuple(issue_ids)
            result = None

    @staticmethod
    def _step_from_response(step: object) -> ViewerProjectionStep:
        if not isinstance(step, Mapping):
            raise XrayProtocolError("Xray test step must be an object")
        action = step.get("action")
        data = step.get("data")
        result = step.get("result")
        if (
            not isinstance(action, str)
            or not isinstance(data, (str, type(None)))
            or not isinstance(result, (str, type(None)))
        ):
            raise XrayProtocolError("Xray test step has invalid fields")
        return ViewerProjectionStep(action, data, result)

    @staticmethod
    def _issue_ids(results: list[object], field: str) -> tuple[str, ...]:
        issue_ids = []
        for result in results:
            if not isinstance(result, Mapping) or not isinstance(result.get("issueId"), str):
                raise XrayProtocolError(f"Xray {field} response contains an invalid issueId")
            issue_ids.append(result["issueId"])
        return tuple(issue_ids)

    async def _graphql(self, query: str, variables: Mapping[str, object]) -> Mapping[str, object]:
        for attempt in range(1, self._settings.max_attempts + 1):
            try:
                response = await self._graphql_once(query, variables)
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as error:
                if attempt == self._settings.max_attempts:
                    raise XrayTransportError("Xray request failed after retries") from error
                await self._backoff(attempt)
                continue
            retry_error = self._retry_error(response)
            if retry_error is not None:
                if attempt == self._settings.max_attempts:
                    raise retry_error
                await self._backoff(attempt)
                continue
            return self._graphql_data(response, self._graphql_operation(query))
        raise XrayTransportError("Xray request has no configured attempts")

    def _retry_error(self, response: httpx.Response) -> XrayProviderError | None:
        if response.status_code == 401:
            self._clear_access_token()
            return XrayAuthenticationError("Xray rejected the access token")
        if response.status_code in _TRANSIENT_STATUS_CODES:
            return XrayTransportError("Xray request failed after retries")
        return None

    @staticmethod
    def _graphql_data(response: httpx.Response, operation: str) -> Mapping[str, object]:
        if response.status_code in {400, 422}:
            raise XrayValidationError(f"Xray rejected {operation} (HTTP {response.status_code})")
        if response.status_code == 403:
            raise XrayAuthorizationError(f"Xray denied {operation} (HTTP 403)")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise XrayProtocolError(
                f"Xray {operation} failed (HTTP {response.status_code})"
            ) from error
        payload = XrayViewerAdapter._json_payload(response, "GraphQL")
        if not isinstance(payload, Mapping):
            raise XrayProtocolError("Xray GraphQL response must be an object")
        if payload.get("errors"):
            raise XrayValidationError(f"Xray {operation} returned GraphQL errors")
        data = payload.get("data")
        if not isinstance(data, Mapping):
            raise XrayProtocolError("Xray GraphQL response does not contain data")
        return data

    async def _graphql_once(self, query: str, variables: Mapping[str, object]) -> httpx.Response:
        if self._client is not None:
            return await self._send_graphql(self._client, query, variables)
        timeout = httpx.Timeout(self._settings.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await self._send_graphql(client, query, variables)

    async def _send_graphql(
        self, client: httpx.AsyncClient, query: str, variables: Mapping[str, object]
    ) -> httpx.Response:
        token = await self._authenticate(client)
        await self._throttle()
        return await client.post(
            self._settings.graphql_url,
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query, "variables": variables},
        )

    async def _authenticate(self, client: httpx.AsyncClient) -> str:
        if self._token_is_valid():
            return self._access_token or ""
        async with self._authentication_lock:
            if self._token_is_valid():
                return self._access_token or ""
            await self._throttle()
            response = await client.post(
                self._settings.auth_url,
                json={
                    "client_id": self._settings.client_id,
                    "client_secret": self._settings.client_secret.get_secret_value(),
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                if response.status_code == 403:
                    raise XrayAuthorizationError(
                        "Xray authentication request was forbidden"
                    ) from error
                raise XrayAuthenticationError("Xray authentication request failed") from error
            payload = self._json_payload(response, "authentication")
            token = self._token_from_payload(payload)
            self._access_token = token
            self._access_token_expires_at = self._token_expiration(token)
            return token

    async def _throttle(self) -> None:
        interval = self._settings.rate_limit_window_seconds / self._settings.rate_limit_requests
        loop = asyncio.get_running_loop()
        async with self._rate_limit_lock:
            now = loop.time()
            wait_seconds = max(0.0, self._next_request_at - now)
            self._next_request_at = max(now, self._next_request_at) + interval
        if wait_seconds:
            await asyncio.sleep(wait_seconds)

    async def _backoff(self, attempt: int) -> None:
        await asyncio.sleep(self._settings.retry_backoff_seconds * (2 ** (attempt - 1)))

    def _token_is_valid(self) -> bool:
        return (
            self._access_token is not None
            and self._access_token_expires_at is not None
            and self._access_token_expires_at > datetime.now(UTC)
        )

    def _clear_access_token(self) -> None:
        self._access_token = None
        self._access_token_expires_at = None

    @staticmethod
    def _graphql_operation(query: str) -> str:
        """Return the declared GraphQL operation name without retaining request data."""
        declaration = query.strip().split("(", 1)[0].split()
        return declaration[-1] if len(declaration) > 1 else "GraphQL operation"

    @staticmethod
    def _token_from_payload(payload: object) -> str:
        if isinstance(payload, str) and payload:
            return payload
        if isinstance(payload, Mapping) and isinstance(payload.get("token"), str):
            return payload["token"]
        raise XrayAuthenticationError("Xray authentication response does not contain a token")

    @staticmethod
    def _token_expiration(token: str) -> datetime:
        try:
            encoded_payload = token.split(".")[1]
            padding = "=" * (-len(encoded_payload) % 4)
            payload = json.loads(base64.urlsafe_b64decode(encoded_payload + padding))
            expires_at = payload["exp"]
            if not isinstance(expires_at, (int, float)):
                raise ValueError("token expiry must be numeric")
            return datetime.fromtimestamp(expires_at, UTC) - timedelta(minutes=1)
        except (IndexError, KeyError, TypeError, ValueError):
            return datetime.now(UTC) + timedelta(hours=23)

    @staticmethod
    def _json_payload(response: httpx.Response, operation: str) -> object:
        try:
            return response.json()
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise XrayProtocolError(f"Xray {operation} response is not valid JSON") from error

    @staticmethod
    def _jira_input(project_key: str, summary: str, description: str | None) -> dict[str, object]:
        fields: dict[str, object] = {"project": {"key": project_key}, "summary": summary}
        if description:
            fields["description"] = description
        return {"fields": fields}

    @staticmethod
    def _step_input(step) -> dict[str, str]:
        return {
            field: value
            for field, value in {
                "action": step.action,
                "data": step.data,
                "result": step.result,
            }.items()
            if value is not None
        }

    @staticmethod
    def _identity(
        payload: Mapping[str, object], mutation: str, entity: str
    ) -> ViewerExternalIdentity:
        mutation_payload = payload.get(mutation)
        if not isinstance(mutation_payload, Mapping):
            raise XrayProtocolError(f"Xray {mutation} response does not contain an entity")
        entity_payload = mutation_payload.get(entity)
        if not isinstance(entity_payload, Mapping):
            raise XrayProtocolError(f"Xray {mutation} response does not contain an entity")
        external_id = entity_payload.get("issueId")
        jira = entity_payload.get("jira")
        external_key = jira.get("key") if isinstance(jira, Mapping) else None
        if not isinstance(external_id, str) or not external_id:
            raise XrayProtocolError(f"Xray {mutation} response does not contain an issueId")
        if not isinstance(external_key, str) or not external_key:
            raise XrayProtocolError(f"Xray {mutation} response does not contain a Jira key")
        return ViewerExternalIdentity(external_id, external_key)

    @staticmethod
    def _results(
        payload: Mapping[str, object], entity_type: ViewerEntityType
    ) -> tuple[object, ...]:
        operation = {
            ViewerEntityType.TEST_CASE: "getTests",
            ViewerEntityType.PRECONDITION: "getPreconditions",
            ViewerEntityType.TEST_SET: "getTestSets",
            ViewerEntityType.TEST_PLAN: "getTestPlans",
        }[entity_type]
        response = payload.get(operation)
        if not isinstance(response, Mapping):
            raise XrayProtocolError(f"Xray {operation} response does not contain results")
        results = response.get("results")
        if not isinstance(results, list):
            raise XrayProtocolError(f"Xray {operation} response does not contain results")
        return tuple(results)

    @staticmethod
    def _read_query(entity_type: ViewerEntityType) -> str:
        return {
            ViewerEntityType.TEST_CASE: XrayViewerAdapter._GET_TESTS,
            ViewerEntityType.PRECONDITION: XrayViewerAdapter._GET_PRECONDITIONS,
            ViewerEntityType.TEST_SET: XrayViewerAdapter._GET_TEST_SETS,
            ViewerEntityType.TEST_PLAN: XrayViewerAdapter._GET_TEST_PLANS,
        }[entity_type]

    _CREATE_TEST = """
        mutation CreateTest($testType: TestTypeInput!, $steps: [CreateTestStepInput!],
            $preconditionIssueIds: [String!], $jira: JSON!) {
          createTest(testType: $testType, steps: $steps,
              preconditionIssueIds: $preconditionIssueIds, jira: $jira) {
            test { issueId jira(fields: [\"key\"]) }
          }
        }
    """
    _CREATE_PRECONDITION = """
                mutation CreatePrecondition($preconditionType: PreconditionTypeInput!,
                        $definition: String!, $jira: JSON!) {
                    createPrecondition(preconditionType: $preconditionType,
                            definition: $definition, jira: $jira) {
            precondition { issueId jira(fields: [\"key\"]) }
          }
        }
    """
    _CREATE_TEST_SET = """
        mutation CreateTestSet($testIssueIds: [String!], $jira: JSON!) {
          createTestSet(testIssueIds: $testIssueIds, jira: $jira) {
            testSet { issueId jira(fields: [\"key\"]) }
          }
        }
    """
    _CREATE_TEST_PLAN = """
        mutation CreateTestPlan($testIssueIds: [String!], $jira: JSON!) {
          createTestPlan(testIssueIds: $testIssueIds, jira: $jira) {
            testPlan { issueId jira(fields: [\"key\"]) }
          }
        }
    """
    _UPDATE_TEST_TYPE = """
        mutation UpdateTestType($issueId: String!, $testType: TestTypeInput!) {
          updateTestType(testIssueId: $issueId, testType: $testType) { warnings }
        }
    """
    _REMOVE_ALL_TEST_STEPS = """
        mutation RemoveAllTestSteps($issueId: String!) {
          removeAllTestSteps(testIssueId: $issueId) { warnings }
        }
    """
    _ADD_TEST_STEP = """
        mutation AddTestStep($issueId: String!, $step: CreateTestStepInput!) {
          addTestStep(testIssueId: $issueId, step: $step) { warnings }
        }
    """
    _ADD_PRECONDITIONS = """
        mutation AddPreconditions($issueId: String!, $preconditionIssueIds: [String!]!) {
                    addPreconditionsToTest(testIssueId: $issueId,
                            preconditionIssueIds: $preconditionIssueIds) { warnings }
        }
    """
    _REMOVE_PRECONDITIONS = """
        mutation RemovePreconditions($issueId: String!, $preconditionIssueIds: [String!]!) {
          removePreconditionsFromTest(testIssueId: $issueId,
              preconditionIssueIds: $preconditionIssueIds) { warnings }
        }
    """
    _UPDATE_PRECONDITION = """
        mutation UpdatePrecondition($issueId: String!, $definition: String!) {
          updatePrecondition(preconditionIssueId: $issueId, definition: $definition) { warnings }
        }
    """
    _ADD_TESTS_TO_SET = """
        mutation AddTestsToTestSet($issueId: String!, $testIssueIds: [String!]!) {
          addTestsToTestSet(testSetIssueId: $issueId, testIssueIds: $testIssueIds) { warnings }
        }
    """
    _ADD_TESTS_TO_PLAN = """
        mutation AddTestsToTestPlan($issueId: String!, $testIssueIds: [String!]!) {
          addTestsToTestPlan(testPlanIssueId: $issueId, testIssueIds: $testIssueIds) { warnings }
        }
    """
    _REMOVE_TESTS_FROM_SET = """
            mutation RemoveTestsFromTestSet($issueId: String!, $testIssueIds: [String!]!) {
                removeTestsFromTestSet(testSetIssueId: $issueId, testIssueIds: $testIssueIds) {
                    warnings
                }
            }
    """
    _REMOVE_TESTS_FROM_PLAN = """
            mutation RemoveTestsFromTestPlan($issueId: String!, $testIssueIds: [String!]!) {
                removeTestsFromTestPlan(testPlanIssueId: $issueId, testIssueIds: $testIssueIds) {
                    warnings
                }
            }
    """
    _GET_TESTS = """
                query GetTests($issueIds: [String!], $limit: Int!, $relationshipLimit: Int!,
                        $relationshipStart: Int!) {
                    getTests(issueIds: $issueIds, limit: $limit) {
                        results { issueId steps { action data result }
                            preconditions(limit: $relationshipLimit, start: $relationshipStart) {
                                total results { issueId }
                            }
                        }
                    }
        }
    """
    _GET_PRECONDITIONS = """
                query GetPreconditions($issueIds: [String!], $limit: Int!, $relationshipLimit: Int!,
                        $relationshipStart: Int!) {
                    getPreconditions(issueIds: $issueIds, limit: $limit) {
                        results { issueId definition }
                    }
        }
    """
    _GET_TEST_SETS = """
                query GetTestSets($issueIds: [String!], $limit: Int!, $relationshipLimit: Int!,
                        $relationshipStart: Int!) {
                    getTestSets(issueIds: $issueIds, limit: $limit) {
                        results {
                            issueId
                            tests(limit: $relationshipLimit, start: $relationshipStart) {
                                total results { issueId }
                            }
                        }
                    }
        }
    """
    _GET_TEST_PLANS = """
                query GetTestPlans($issueIds: [String!], $limit: Int!, $relationshipLimit: Int!,
                        $relationshipStart: Int!) {
                    getTestPlans(issueIds: $issueIds, limit: $limit) {
                        results {
                            issueId
                            tests(limit: $relationshipLimit, start: $relationshipStart) {
                                total results { issueId }
                            }
                        }
                    }
        }
    """
