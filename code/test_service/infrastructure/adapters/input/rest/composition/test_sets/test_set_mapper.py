"""Mapping between the Composition REST contract and Test Set domain types."""

from datetime import datetime
from uuid import UUID

from test_service_server.models.create_test_set_request import CreateTestSetRequest
from test_service_server.models.project_reference import ProjectReference
from test_service_server.models.test_set import TestSet as ApiTestSet
from test_service_server.models.test_set_list_response import TestSetListResponse
from test_service_server.models.test_set_version_list_response import TestSetVersionListResponse

from test_service.domain.application.commands.composition import (
    ActivateTestSetCommand,
    CreateTestSetCommand,
    CreateTestSetVersionCommand,
    DeprecateTestSetCommand,
)
from test_service.domain.application.queries.composition import (
    ListTestSetsQuery,
    ListTestSetVersionsQuery,
    TestSetQuery,
)
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.input.rest.versioned_resource_mapper import (
    VersionedResourceMapper,
)


class TestSetMapper:
    """Translate generated Composition models to Test Set commands and responses."""

    @staticmethod
    def to_create_command(
        project_key: str, request: CreateTestSetRequest, identity: str, requested_at: datetime
    ) -> CreateTestSetCommand:
        return CreateTestSetCommand(
            project_key=project_key,
            set_key=request.set_key,
            **TestSetMapper._request_fields(request, identity, requested_at),
        )

    @staticmethod
    def to_create_version_command(
        project_key: str,
        source_id: UUID,
        request: CreateTestSetRequest,
        identity: str,
        requested_at: datetime,
    ) -> CreateTestSetVersionCommand:
        return CreateTestSetVersionCommand(
            source_id=source_id,
            project_key=project_key,
            set_key=request.set_key,
            **TestSetMapper._request_fields(request, identity, requested_at),
        )

    @staticmethod
    def to_pagination(
        offset: int | None, limit: int | None, sort_by: str | None, order
    ) -> PaginationParams:
        return VersionedResourceMapper.to_pagination(offset, limit, sort_by, order)

    @staticmethod
    def to_status(value: str | None) -> VersionStatus | None:
        return VersionedResourceMapper.to_status(value)

    @staticmethod
    def to_get_query(project_key: str, identifier: UUID) -> TestSetQuery:
        return TestSetQuery(project_key, identifier)

    @staticmethod
    def to_activate_command(
        project_key: str, identifier: UUID, reason: str | None
    ) -> ActivateTestSetCommand:
        return ActivateTestSetCommand(project_key, identifier, reason)

    @staticmethod
    def to_deprecate_command(
        project_key: str, identifier: UUID, reason: str | None
    ) -> DeprecateTestSetCommand:
        return DeprecateTestSetCommand(project_key, identifier, reason)

    @staticmethod
    def to_list_query(
        project_key: str, pagination: PaginationParams, status: VersionStatus | None
    ) -> ListTestSetsQuery:
        return ListTestSetsQuery(project_key, pagination, status)

    @staticmethod
    def to_versions_query(
        project_key: str,
        set_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None,
    ) -> ListTestSetVersionsQuery:
        return ListTestSetVersionsQuery(project_key, set_key, pagination, status)

    @staticmethod
    def to_api(test_set: TestSet, project_name: str) -> ApiTestSet:
        return ApiTestSet(
            id=test_set.identifier,
            project=ProjectReference(key=test_set.project_key, name=project_name),
            setKey=test_set.set_key,
            version=test_set.version,
            name=test_set.name,
            description=test_set.description,
            status=test_set.status.value,
            items=list(test_set.items),
            createdAt=test_set.created_at,
            createdBy=test_set.created_by,
        )

    @staticmethod
    def to_list_response(
        page: Page[TestSet], project_name: str, pagination: PaginationParams
    ) -> TestSetListResponse:
        return VersionedResourceMapper.to_response(
            TestSetListResponse, page, project_name, pagination, TestSetMapper.to_api
        )

    @staticmethod
    def to_version_list_response(
        page: Page[TestSet], project_name: str, pagination: PaginationParams
    ) -> TestSetVersionListResponse:
        return VersionedResourceMapper.to_response(
            TestSetVersionListResponse, page, project_name, pagination, TestSetMapper.to_api
        )

    @staticmethod
    def _request_fields(
        request: CreateTestSetRequest, identity: str, requested_at: datetime
    ) -> dict:
        return {
            "name": request.name,
            "description": request.description,
            "items": tuple(request.items),
            "requested_by": identity,
            "requested_at": requested_at,
        }
