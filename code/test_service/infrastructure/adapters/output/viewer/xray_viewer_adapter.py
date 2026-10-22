"""Direct Xray Cloud GraphQL adapter for Viewer projection and drift operations."""

import asyncio
import base64
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

import httpx

from test_service.config import XraySettings
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin
from test_service.domain.model.exceptions.permanent_viewer_result_publication_exception import (
    PermanentViewerResultPublicationError,
)
from test_service.domain.model.exceptions.retryable_viewer_result_publication_exception import (
    RetryableViewerResultPublicationError,
)
from test_service.domain.model.execution.execution import ExecutionStatus, ResultStatus
from test_service.domain.model.viewer.execution_result_projection import (
    ViewerExecutionResultIdentity,
    ViewerExecutionResultProjection,
)
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
from test_service.domain.ports.output.viewer.viewer_result_publisher_port import (
    ViewerResultPublisherPort,
)
from test_service.infrastructure.adapters.output.viewer.xray_exceptions import (
    XrayAuthenticationError,
    XrayAuthorizationError,
    XrayProtocolError,
    XrayProviderError,
    XrayTransportError,
    XrayValidationError,
)

_TRANSIENT_STATUS_CODES = frozenset({429, 502, 503, 504})
_SENSITIVE_GRAPHQL_VALUE = re.compile(
    r"(?i)(authorization|bearer|token|secret|api[_-]?key|password)"
    r"(\s*[:=]\s*)(?:bearer\s+)?[^\s,;\"'}]+"
)


class XrayViewerAdapter(ViewerPublisherPort, ViewerDriftDetectorPort, ViewerResultPublisherPort):
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
            if await self._remote_entity_exists(projection):
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
            self._read_variables(record.entity_type, record.external_entity_id),
        )
        results = self._results(payload, record.entity_type)
        if not results:
            return DriftObservation(DriftType.DELETED, None)
        remote_state = await self._remote_state(projection, results[0])
        differences = ViewerManagedState.from_projection(projection).differing_fields(remote_state)
        if differences:
            return DriftObservation(DriftType.MODIFIED, {"fields": differences})
        return None

    async def publish_execution_result(
        self, projection: ViewerExecutionResultProjection
    ) -> ViewerExecutionResultIdentity:
        """Create or reuse one Xray Test Execution and update its Test Runs."""
        try:
            execution = await self._execution_identity(projection)
            test_run_ids = await self._test_run_ids(
                execution.external_id,
                tuple(test_run.external_test_id for test_run in projection.test_runs),
            )
            for test_run in projection.test_runs:
                test_run_id = test_run_ids.get(test_run.external_test_id)
                if test_run_id is None:
                    raise XrayProtocolError(
                        "Xray did not create a Test Run for a synchronized Test."
                    )
                await self._update_test_run(test_run_id, test_run, projection.execution_status)
            return ViewerExecutionResultIdentity(
                execution_id=execution.external_id,
                execution_key=execution.external_key,
                test_run_ids={
                    test_run.test_result_id: test_run_ids[test_run.external_test_id]
                    for test_run in projection.test_runs
                },
            )
        except XrayTransportError as error:
            raise RetryableViewerResultPublicationError(
                "Xray result publication could not be completed.",
                origin=ErrorOrigin.PROVIDER,
                provider_name="Xray",
            ) from error
        except XrayProviderError as error:
            raise PermanentViewerResultPublicationError(
                self._redact_graphql_message(str(error)) or "Xray rejected the result publication.",
                origin=ErrorOrigin.PROVIDER,
                provider_name="Xray",
            ) from error

    async def _execution_identity(
        self, projection: ViewerExecutionResultProjection
    ) -> ViewerExternalIdentity:
        publication = projection.publication
        if publication.external_execution_id and publication.external_execution_key:
            return ViewerExternalIdentity(
                publication.external_execution_id,
                publication.external_execution_key,
            )
        existing = await self._find_execution_by_correlation(
            publication.project_key, publication.correlation_key
        )
        if existing is not None:
            return existing
        variables = {
            "testIssueIds": [test_run.external_test_id for test_run in projection.test_runs],
            "testEnvironments": [projection.environment_name],
            "jira": {
                "fields": {
                    "project": {"key": publication.project_key},
                    "summary": projection.summary,
                    "labels": [publication.correlation_key],
                }
            },
        }
        payload = await self._graphql(self._CREATE_TEST_EXECUTION, variables)
        return self._identity(payload, "createTestExecution", "testExecution")

    async def _find_execution_by_correlation(
        self, project_key: str, correlation_key: str
    ) -> ViewerExternalIdentity | None:
        payload = await self._graphql(
            self._GET_TEST_EXECUTIONS,
            {"jql": f'project = "{project_key}" AND labels = "{correlation_key}"', "limit": 1},
        )
        response = payload.get("getTestExecutions")
        if not isinstance(response, Mapping):
            raise XrayProtocolError("Xray Test Execution query does not contain a response.")
        results = response.get("results")
        if not isinstance(results, list):
            raise XrayProtocolError("Xray Test Execution query does not contain results.")
        if not results:
            return None
        return self._execution_identity_from_result(results[0])

    async def _test_run_ids(
        self, execution_id: str, test_issue_ids: tuple[str, ...]
    ) -> dict[str, str]:
        payload = await self._graphql(
            self._GET_TEST_RUNS,
            {
                "testExecutionIssueIds": [execution_id],
                "testIssueIds": list(test_issue_ids),
                "limit": len(test_issue_ids),
            },
        )
        response = payload.get("getTestRuns")
        if not isinstance(response, Mapping):
            raise XrayProtocolError("Xray Test Run query does not contain a response.")
        results = response.get("results")
        if not isinstance(results, list):
            raise XrayProtocolError("Xray Test Run query does not contain results.")
        test_run_ids: dict[str, str] = {}
        for result in results:
            if not isinstance(result, Mapping):
                raise XrayProtocolError("Xray Test Run query returned an invalid Test Run.")
            identifier = result.get("id")
            test = result.get("test")
            issue_id = test.get("issueId") if isinstance(test, Mapping) else None
            if not isinstance(identifier, str) or not isinstance(issue_id, str):
                raise XrayProtocolError("Xray Test Run query returned an invalid identity.")
            test_run_ids[issue_id] = identifier
        return test_run_ids

    async def _update_test_run(
        self, test_run_id: str, test_run, execution_status: ExecutionStatus
    ) -> None:
        await self._graphql(
            self._UPDATE_TEST_RUN_STATUS,
            {
                "id": test_run_id,
                "status": self._xray_test_run_status(test_run.status, execution_status),
            },
        )
        comment = self._test_run_comment(test_run.comment, test_run.duration_ms)
        await self._graphql(
            self._UPDATE_TEST_RUN_DETAILS,
            {
                "id": test_run_id,
                "testRun": {
                    "comment": comment,
                    "startedOn": (test_run.started_at.isoformat() if test_run.started_at else None),
                    "finishedOn": (
                        test_run.finished_at.isoformat() if test_run.finished_at else None
                    ),
                },
            },
        )

    @staticmethod
    def _test_run_comment(comment: str | None, duration_ms: int | None) -> str:
        duration = (
            f"Duration: {duration_ms} ms" if duration_ms is not None else "Duration: unavailable"
        )
        return f"{duration}\n{comment}"[:1000] if comment else duration

    @staticmethod
    def _xray_test_run_status(
        result_status: ResultStatus, execution_status: ExecutionStatus
    ) -> str:
        if execution_status is ExecutionStatus.CANCELLED and result_status is ResultStatus.SKIPPED:
            return "ABORTED"
        return {
            ResultStatus.PASSED: "PASS",
            ResultStatus.FAILED: "FAIL",
            ResultStatus.ERROR: "FAIL",
            ResultStatus.BLOCKED: "ABORTED",
            ResultStatus.SKIPPED: "TODO",
        }[result_status]

    @staticmethod
    def _execution_identity_from_result(result: object) -> ViewerExternalIdentity:
        if not isinstance(result, Mapping):
            raise XrayProtocolError("Xray Test Execution query returned an invalid entity.")
        issue_id = result.get("issueId")
        jira = result.get("jira")
        key = jira.get("key") if isinstance(jira, Mapping) else None
        if not isinstance(issue_id, str) or not isinstance(key, str):
            raise XrayProtocolError("Xray Test Execution query returned an invalid identity.")
        return ViewerExternalIdentity(issue_id, key)

    async def _create_projection(self, projection: ViewerProjection) -> ViewerExternalIdentity:
        record = projection.record
        variables: dict[str, object] = {
            "jira": self._jira_input(
                record.project_key, projection.summary, projection.description, projection.labels
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
            identity = self._identity(payload, "createTest", "test")
            await self._synchronize_test_preconditions(
                identity.external_id, projection.precondition_external_ids
            )
            return identity
        if record.entity_type is ViewerEntityType.PRECONDITION:
            variables.update(
                {
                    "preconditionType": {"name": "Manual"},
                    "definition": projection.definition or "",
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
            await self._synchronize_test_preconditions(
                issue_id, projection.precondition_external_ids
            )
            return
        if record.entity_type is ViewerEntityType.PRECONDITION:
            await self._graphql(
                self._UPDATE_PRECONDITION,
                {
                    "issueId": issue_id,
                    "definition": projection.definition or "",
                },
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

    async def _remote_entity_exists(self, projection: ViewerProjection) -> bool:
        record = projection.record
        issue_id = record.external_entity_id
        if issue_id is None:
            return False
        payload = await self._graphql(
            self._read_query(record.entity_type),
            self._read_variables(record.entity_type, issue_id),
        )
        return bool(self._results(payload, record.entity_type))

    async def _synchronize_test_preconditions(
        self, test_issue_id: str, expected_issue_ids: tuple[str, ...]
    ) -> None:
        current_issue_ids = await self._relationship_issue_ids(
            ViewerEntityType.TEST_CASE, test_issue_id, "preconditions"
        )
        stale_issue_ids = tuple(
            issue_id for issue_id in current_issue_ids if issue_id not in expected_issue_ids
        )
        if stale_issue_ids:
            await self._graphql(
                self._REMOVE_PRECONDITIONS,
                {"issueId": test_issue_id, "preconditionIssueIds": list(stale_issue_ids)},
            )
        missing_issue_ids = tuple(
            issue_id for issue_id in expected_issue_ids if issue_id not in current_issue_ids
        )
        if missing_issue_ids:
            await self._graphql(
                self._ADD_PRECONDITIONS,
                {"issueId": test_issue_id, "preconditionIssueIds": list(missing_issue_ids)},
            )

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
                    self._read_variables(entity_type, issue_id, start),
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
            detail = XrayViewerAdapter._graphql_error_detail(response)
            raise XrayValidationError(
                f"Xray rejected {operation} (HTTP {response.status_code}){detail}"
            )
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
            detail = XrayViewerAdapter._graphql_errors_detail(payload.get("errors"))
            raise XrayValidationError(f"Xray {operation} returned GraphQL errors{detail}")
        data = payload.get("data")
        if not isinstance(data, Mapping):
            raise XrayProtocolError("Xray GraphQL response does not contain data")
        return data

    @staticmethod
    def _graphql_error_detail(response: httpx.Response) -> str:
        """Extract provider diagnostics without retaining response payloads or secrets."""
        try:
            payload = response.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            return ""
        if not isinstance(payload, Mapping):
            return ""
        return XrayViewerAdapter._graphql_errors_detail(payload.get("errors"))

    @staticmethod
    def _graphql_errors_detail(errors: object) -> str:
        """Return the safe, human-readable messages exposed by GraphQL errors."""
        if not isinstance(errors, list):
            return ""
        messages = [
            XrayViewerAdapter._redact_graphql_message(error.get("message"))
            for error in errors
            if isinstance(error, Mapping) and isinstance(error.get("message"), str)
        ]
        safe_messages = [message for message in messages if message]
        if not safe_messages:
            return ""
        return f": {'; '.join(safe_messages[:3])}"[:500]

    @staticmethod
    def _redact_graphql_message(message: object) -> str:
        if not isinstance(message, str):
            return ""
        return _SENSITIVE_GRAPHQL_VALUE.sub(r"\1\2[REDACTED]", message)[:300]

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
    def _jira_input(
        project_key: str, summary: str, description: str | None, labels: tuple[str, ...]
    ) -> dict[str, object]:
        fields: dict[str, object] = {"project": {"key": project_key}, "summary": summary}
        if description:
            fields["description"] = description
        if labels:
            fields["labels"] = list(labels)
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

    @staticmethod
    def _read_variables(
        entity_type: ViewerEntityType, issue_id: str, relationship_start: int = 0
    ) -> dict[str, object]:
        variables: dict[str, object] = {"issueIds": [issue_id], "limit": 1}
        if entity_type is not ViewerEntityType.PRECONDITION:
            variables.update({"relationshipLimit": 100, "relationshipStart": relationship_start})
        return variables

    _CREATE_TEST = """
        mutation CreateTest($testType: UpdateTestTypeInput, $steps: [CreateStepInput],
            $preconditionIssueIds: [String!], $jira: JSON!) {
          createTest(testType: $testType, steps: $steps,
              preconditionIssueIds: $preconditionIssueIds, jira: $jira) {
            test { issueId jira(fields: [\"key\"]) }
          }
        }
    """
    _CREATE_TEST_EXECUTION = """
                mutation CreateTestExecution($testIssueIds: [String!], $testEnvironments: [String!],
                        $jira: JSON!) {
                        createTestExecution(testIssueIds: $testIssueIds,
                            testEnvironments: $testEnvironments, jira: $jira) {
                        testExecution { issueId jira(fields: [\"key\"]) }
                    }
                }
        """
    _GET_TEST_EXECUTIONS = """
                query GetTestExecutions($jql: String!, $limit: Int!) {
                    getTestExecutions(jql: $jql, limit: $limit) {
                        results { issueId jira(fields: [\"key\"]) }
                    }
                }
        """
    _GET_TEST_RUNS = """
                query GetTestRuns($testExecutionIssueIds: [String!], $testIssueIds: [String!],
                        $limit: Int!) {
                    getTestRuns(testExecutionIssueIds: $testExecutionIssueIds,
                            testIssueIds: $testIssueIds, limit: $limit) {
                        results { id test { issueId } }
                    }
                }
        """
    _UPDATE_TEST_RUN_STATUS = """
                mutation UpdateTestRunStatus($id: String!, $status: String!) {
                    updateTestRunStatus(id: $id, status: $status) { id }
                }
        """
    _UPDATE_TEST_RUN_DETAILS = """
                mutation UpdateTestRun($id: String!, $testRun: UpdateTestRunInput!) {
                    updateTestRun(id: $id, testRun: $testRun) { id }
                }
        """
    _CREATE_PRECONDITION = """
            mutation CreatePrecondition($preconditionType: UpdatePreconditionTypeInput,
                $definition: String, $jira: JSON!) {
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
        mutation UpdateTestType($issueId: String!, $testType: UpdateTestTypeInput!) {
                    updateTestType(issueId: $issueId, testType: $testType) { issueId }
        }
    """
    _REMOVE_ALL_TEST_STEPS = """
        mutation RemoveAllTestSteps($issueId: String!) {
                    removeAllTestSteps(issueId: $issueId)
        }
    """
    _ADD_TEST_STEP = """
        mutation AddTestStep($issueId: String!, $step: CreateStepInput!) {
                    addTestStep(issueId: $issueId, step: $step) { id }
        }
    """
    _ADD_PRECONDITIONS = """
        mutation AddPreconditions($issueId: String!, $preconditionIssueIds: [String!]!) {
                    addPreconditionsToTest(issueId: $issueId,
                            preconditionIssueIds: $preconditionIssueIds) {
                        addedPreconditions
                        warning
                    }
        }
    """
    _REMOVE_PRECONDITIONS = """
        mutation RemovePreconditions($issueId: String!, $preconditionIssueIds: [String!]!) {
          removePreconditionsFromTest(issueId: $issueId,
              preconditionIssueIds: $preconditionIssueIds)
        }
    """
    _UPDATE_PRECONDITION = """
        mutation UpdatePrecondition($issueId: String!, $definition: String!) {
          updatePrecondition(issueId: $issueId, data: { definition: $definition }) {
            issueId
          }
        }
    """
    _ADD_TESTS_TO_SET = """
        mutation AddTestsToTestSet($issueId: String!, $testIssueIds: [String!]!) {
                    addTestsToTestSet(issueId: $issueId, testIssueIds: $testIssueIds) {
                        addedTests
                        warning
                    }
        }
    """
    _ADD_TESTS_TO_PLAN = """
        mutation AddTestsToTestPlan($issueId: String!, $testIssueIds: [String!]!) {
                    addTestsToTestPlan(issueId: $issueId, testIssueIds: $testIssueIds) {
                        addedTests
                        warning
                    }
        }
    """
    _REMOVE_TESTS_FROM_SET = """
                mutation RemoveTestsFromTestSet($issueId: String!, $testIssueIds: [String!]!) {
                    removeTestsFromTestSet(issueId: $issueId, testIssueIds: $testIssueIds)
                }
    """
    _REMOVE_TESTS_FROM_PLAN = """
                mutation RemoveTestsFromTestPlan($issueId: String!, $testIssueIds: [String!]!) {
                    removeTestsFromTestPlan(issueId: $issueId, testIssueIds: $testIssueIds)
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
            query GetPreconditions($issueIds: [String!], $limit: Int!) {
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
