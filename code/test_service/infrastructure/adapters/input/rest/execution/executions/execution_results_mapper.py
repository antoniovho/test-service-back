"""Mapping between generated execution-result REST models and domain types."""

from uuid import UUID

from test_service_server.models.action_result import ActionResult as ApiActionResult
from test_service_server.models.action_result_list_response import ActionResultListResponse
from test_service_server.models.pagination import Pagination as ApiPagination
from test_service_server.models.test_result import TestResult as ApiTestResult
from test_service_server.models.test_result_artifact import (
    TestResultArtifact as ApiTestResultArtifact,
)
from test_service_server.models.test_result_artifact_list_response import (
    TestResultArtifactListResponse,
)
from test_service_server.models.test_result_list_response import TestResultListResponse

from test_service.domain.application.queries.execution import (
    ExecutionResultQuery,
    ListExecutionResultActionsQuery,
    ListExecutionResultArtifactsQuery,
    ListExecutionResultsQuery,
)
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.commons.pagination import SortOrder as DomainSortOrder
from test_service.domain.model.execution.execution import (
    ActionResult,
    TestResult,
    TestResultArtifact,
)


class ExecutionResultsMapper:
    """Translate between the result REST contract and immutable domain values."""

    _RESULT_SORT_FIELDS = {
        "createdAt": "created_at",
        "startedAt": "started_at",
        "finishedAt": "finished_at",
        "durationMs": "duration_ms",
        "status": "status",
    }
    _ARTIFACT_SORT_FIELDS = {
        "createdAt": "created_at",
        "artifactType": "artifact_type",
        "storageType": "storage_type",
        "sizeBytes": "size_bytes",
    }

    @staticmethod
    def to_list_results_query(
        project_key: str, execution_id: UUID, offset: int | None, limit: int | None, sort_by, order
    ) -> ListExecutionResultsQuery:
        return ListExecutionResultsQuery(
            project_key=project_key,
            execution_id=execution_id,
            pagination=ExecutionResultsMapper._pagination(
                offset, limit, sort_by, order, ExecutionResultsMapper._RESULT_SORT_FIELDS
            ),
        )

    @staticmethod
    def to_get_result_query(
        project_key: str, execution_id: UUID, test_result_id: UUID
    ) -> ExecutionResultQuery:
        return ExecutionResultQuery(project_key, execution_id, test_result_id)

    @staticmethod
    def to_list_actions_query(
        project_key: str,
        execution_id: UUID,
        test_result_id: UUID,
        offset: int | None,
        limit: int | None,
        sort_by,
        order,
    ) -> ListExecutionResultActionsQuery:
        return ListExecutionResultActionsQuery(
            project_key,
            execution_id,
            test_result_id,
            ExecutionResultsMapper._pagination(
                offset, limit, sort_by, order, ExecutionResultsMapper._RESULT_SORT_FIELDS
            ),
        )

    @staticmethod
    def to_list_artifacts_query(
        project_key: str,
        execution_id: UUID,
        test_result_id: UUID,
        offset: int | None,
        limit: int | None,
        sort_by,
        order,
    ) -> ListExecutionResultArtifactsQuery:
        return ListExecutionResultArtifactsQuery(
            project_key,
            execution_id,
            test_result_id,
            ExecutionResultsMapper._pagination(
                offset, limit, sort_by, order, ExecutionResultsMapper._ARTIFACT_SORT_FIELDS
            ),
        )

    @staticmethod
    def to_test_result_api(test_result: TestResult) -> ApiTestResult:
        return ApiTestResult(
            id=test_result.identifier,
            executionId=test_result.execution_id,
            testCaseId=test_result.test_case_id,
            status=test_result.status.value,
            startedAt=test_result.started_at,
            finishedAt=test_result.finished_at,
            durationMs=test_result.duration_ms,
            errorCode=test_result.error_code,
            errorMessage=test_result.error_message,
            createdAt=test_result.created_at,
        )

    @staticmethod
    def to_action_result_api(action_result: ActionResult) -> ApiActionResult:
        return ApiActionResult(
            id=action_result.identifier,
            testResultId=action_result.test_result_id,
            actionId=action_result.action_id,
            actionType=action_result.action_type,
            status=action_result.status.value,
            startedAt=action_result.started_at,
            finishedAt=action_result.finished_at,
            durationMs=action_result.duration_ms,
            expected=dict(action_result.expected) if action_result.expected is not None else None,
            actual=dict(action_result.actual) if action_result.actual is not None else None,
            output=dict(action_result.output) if action_result.output is not None else None,
            errorCode=action_result.error_code,
            errorMessage=action_result.error_message,
            createdAt=action_result.created_at,
        )

    @staticmethod
    def to_artifact_api(artifact: TestResultArtifact) -> ApiTestResultArtifact:
        return ApiTestResultArtifact(
            id=artifact.identifier,
            testResultId=artifact.test_result_id,
            actionResultId=artifact.action_result_id,
            artifactType=artifact.artifact_type.value,
            storageType=artifact.storage_type.value,
            storageUri=artifact.storage_uri,
            contentHash=artifact.content_hash,
            sizeBytes=artifact.size_bytes,
            mimeType=artifact.mime_type,
            createdAt=artifact.created_at,
        )

    @staticmethod
    def to_test_result_list_response(
        page: Page[TestResult], pagination: PaginationParams
    ) -> TestResultListResponse:
        return TestResultListResponse(
            data=[ExecutionResultsMapper.to_test_result_api(item) for item in page.items],
            pagination=ExecutionResultsMapper._api_pagination(page, pagination),
        )

    @staticmethod
    def to_action_result_list_response(
        page: Page[ActionResult], pagination: PaginationParams
    ) -> ActionResultListResponse:
        return ActionResultListResponse(
            data=[ExecutionResultsMapper.to_action_result_api(item) for item in page.items],
            pagination=ExecutionResultsMapper._api_pagination(page, pagination),
        )

    @staticmethod
    def to_artifact_list_response(
        page: Page[TestResultArtifact], pagination: PaginationParams
    ) -> TestResultArtifactListResponse:
        return TestResultArtifactListResponse(
            data=[ExecutionResultsMapper.to_artifact_api(item) for item in page.items],
            pagination=ExecutionResultsMapper._api_pagination(page, pagination),
        )

    @staticmethod
    def _pagination(offset, limit, sort_by, order, sort_fields) -> PaginationParams:
        return PaginationParams(
            offset=offset if offset is not None else 0,
            limit=limit if limit is not None else 20,
            sort_by=sort_fields.get(sort_by or "createdAt", "created_at"),
            order=DomainSortOrder(order.value) if order is not None else DomainSortOrder.ASC,
        )

    @staticmethod
    def _api_pagination(page, pagination: PaginationParams) -> ApiPagination:
        return ApiPagination(offset=pagination.offset, limit=pagination.limit, total=page.total)
