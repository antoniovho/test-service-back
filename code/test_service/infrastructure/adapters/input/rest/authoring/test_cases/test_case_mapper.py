"""Mapping between the Authoring REST contract and Test Case domain types."""

from datetime import datetime

from test_service_server.models.action import Action as ApiAction
from test_service_server.models.create_test_case_request import CreateTestCaseRequest
from test_service_server.models.definition import Definition as ApiDefinition
from test_service_server.models.pagination import Pagination as ApiPagination
from test_service_server.models.precondition_reference import (
    PreconditionReference as ApiPreconditionReference,
)
from test_service_server.models.project_reference import ProjectReference
from test_service_server.models.test_case import TestCase as ApiTestCase
from test_service_server.models.test_case_list_response import TestCaseListResponse
from test_service_server.models.test_case_version_list_response import TestCaseVersionListResponse

from test_service.domain.application.commands.authoring import (
    ActivateTestCaseCommand,
    CreateTestCaseCommand,
    CreateTestCaseVersionCommand,
    DeprecateTestCaseCommand,
)
from test_service.domain.application.queries.authoring import (
    ListTestCasesQuery,
    TestCaseQuery,
    TestCaseVersionsQuery,
)
from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import (
    Priority,
    TestCase,
    TestLevel,
    TestType,
)
from test_service.domain.model.lifecycle import VersionStatus


class TestCaseMapper:
    """Translate generated Authoring models to Test Case commands and responses."""

    @staticmethod
    def to_create_command(
        project_key: str, request: CreateTestCaseRequest, identity: str, requested_at: datetime
    ) -> CreateTestCaseCommand:
        return CreateTestCaseCommand(
            project_key=project_key,
            test_key=request.test_key,
            **TestCaseMapper._request_fields(request, identity, requested_at),
        )

    @staticmethod
    def to_create_version_command(
        project_key: str,
        source_id,
        request: CreateTestCaseRequest,
        identity: str,
        requested_at: datetime,
    ) -> CreateTestCaseVersionCommand:
        return CreateTestCaseVersionCommand(
            source_id=source_id,
            project_key=project_key,
            **TestCaseMapper._request_fields(request, identity, requested_at),
        )

    @staticmethod
    def to_pagination(
        offset: int | None, limit: int | None, sort_by: str | None, order
    ) -> PaginationParams:
        return PaginationParams(
            offset=offset or 0,
            limit=limit or 20,
            sort_by={"version": "version", "createdAt": "created_at"}.get(
                sort_by or "version", "version"
            ),
            order=SortOrder(order.value) if order is not None else SortOrder.ASC,
        )

    @staticmethod
    def to_status(value: str | None) -> VersionStatus | None:
        return VersionStatus(value) if value is not None else None

    @staticmethod
    def to_get_query(project_key: str, identifier) -> TestCaseQuery:
        return TestCaseQuery(project_key, identifier)

    @staticmethod
    def to_activate_command(
        project_key: str, identifier, reason: str | None
    ) -> ActivateTestCaseCommand:
        return ActivateTestCaseCommand(
            project_key=project_key, identifier=identifier, reason=reason
        )

    @staticmethod
    def to_deprecate_command(
        project_key: str, identifier, reason: str | None
    ) -> DeprecateTestCaseCommand:
        return DeprecateTestCaseCommand(
            project_key=project_key, identifier=identifier, reason=reason
        )

    @staticmethod
    def to_list_query(
        project_key: str, pagination: PaginationParams, status: VersionStatus | None
    ) -> ListTestCasesQuery:
        return ListTestCasesQuery(project_key=project_key, pagination=pagination, status=status)

    @staticmethod
    def to_versions_query(
        project_key: str, test_key: str, pagination: PaginationParams, status: VersionStatus | None
    ) -> TestCaseVersionsQuery:
        return TestCaseVersionsQuery(
            project_key=project_key, test_key=test_key, pagination=pagination, status=status
        )

    @staticmethod
    def to_api(test_case: TestCase, project_name: str) -> ApiTestCase:
        return ApiTestCase(
            id=test_case.identifier,
            project=ProjectReference(key=test_case.project_key, name=project_name),
            testKey=test_case.test_key,
            version=test_case.version,
            name=test_case.name,
            summary=test_case.summary,
            objective=test_case.objective,
            testType=test_case.test_type.value,
            testLevel=test_case.test_level.value,
            priority=test_case.priority.value,
            status=test_case.status.value,
            definition=ApiDefinition(
                schemaVersion=test_case.definition.schema_version,
                variables=dict(test_case.definition.variables),
                actions=[
                    ApiAction(
                        id=action.identifier,
                        type=action.action_type,
                        source=action.source,
                        config=dict(action.configuration),
                    )
                    for action in test_case.definition.actions
                ],
            ),
            preconditions=[
                ApiPreconditionReference(
                    id=reference.identifier,
                    preconditionKey=reference.precondition_key,
                    version=reference.version,
                )
                for reference in test_case.preconditions
            ],
            timeoutSeconds=test_case.timeout_seconds,
            createdAt=test_case.created_at,
            createdBy=test_case.created_by,
            metadata=dict(test_case.metadata or {}),
        )

    @staticmethod
    def to_list_response(
        page: Page[TestCase], project_name: str, pagination: PaginationParams
    ) -> TestCaseListResponse:
        return TestCaseListResponse(
            data=[TestCaseMapper.to_api(test_case, project_name) for test_case in page.items],
            pagination=TestCaseMapper._to_api_pagination(pagination, page.total),
        )

    @staticmethod
    def to_version_list_response(
        page: Page[TestCase], project_name: str, pagination: PaginationParams
    ) -> TestCaseVersionListResponse:
        return TestCaseVersionListResponse(
            data=[TestCaseMapper.to_api(test_case, project_name) for test_case in page.items],
            pagination=TestCaseMapper._to_api_pagination(pagination, page.total),
        )

    @staticmethod
    def _request_fields(
        request: CreateTestCaseRequest, identity: str, requested_at: datetime
    ) -> dict:
        return {
            "name": request.name,
            "summary": request.summary,
            "objective": request.objective,
            "test_type": TestType(request.test_type),
            "test_level": TestLevel(request.test_level),
            "priority": Priority(request.priority),
            "definition": TestCaseMapper._definition_to_domain(request.definition),
            "timeout_seconds": request.timeout_seconds,
            "requested_by": identity,
            "requested_at": requested_at,
            "preconditions": tuple(reference.id for reference in request.preconditions or []),
            "metadata": request.metadata,
        }

    @staticmethod
    def _definition_to_domain(definition: ApiDefinition) -> Definition:
        return Definition(
            schema_version=definition.schema_version,
            variables=definition.variables,
            actions=tuple(
                TestCaseMapper._action_to_domain(action) for action in definition.actions
            ),
        )

    @staticmethod
    def _action_to_domain(action: ApiAction) -> Action:
        return Action(
            identifier=action.id,
            action_type=action.type,
            source=action.source,
            configuration=action.config,
        )

    @staticmethod
    def _to_api_pagination(pagination: PaginationParams, total: int) -> ApiPagination:
        return ApiPagination(offset=pagination.offset, limit=pagination.limit, total=total)
