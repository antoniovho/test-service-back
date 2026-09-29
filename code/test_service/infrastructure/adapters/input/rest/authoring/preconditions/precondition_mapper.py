"""Mapping between the Authoring REST contract and Precondition domain types."""

from datetime import datetime

from test_service_server.models.action import Action as ApiAction
from test_service_server.models.create_precondition_request import CreatePreconditionRequest
from test_service_server.models.definition import Definition as ApiDefinition
from test_service_server.models.pagination import Pagination as ApiPagination
from test_service_server.models.precondition import Precondition as ApiPrecondition
from test_service_server.models.precondition_list_response import PreconditionListResponse
from test_service_server.models.project_reference import ProjectReference

from test_service.domain.application.commands.authoring import (
    ActivatePreconditionCommand,
    CreatePreconditionCommand,
    CreatePreconditionVersionCommand,
    DeprecatePreconditionCommand,
)
from test_service.domain.application.queries.authoring import (
    ListPreconditionsQuery,
    PreconditionQuery,
    PreconditionVersionsQuery,
)
from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.lifecycle import VersionStatus


class PreconditionMapper:
    """Translate generated Authoring models to Precondition commands and queries."""

    @staticmethod
    def to_create_command(
        project_key: str, request: CreatePreconditionRequest, identity: str, requested_at: datetime
    ) -> CreatePreconditionCommand:
        return CreatePreconditionCommand(
            project_key=project_key,
            precondition_key=request.precondition_key,
            **PreconditionMapper._request_fields(request, identity, requested_at),
        )

    @staticmethod
    def to_create_version_command(
        project_key: str,
        source_id,
        request: CreatePreconditionRequest,
        identity: str,
        requested_at: datetime,
    ) -> CreatePreconditionVersionCommand:
        return CreatePreconditionVersionCommand(
            source_id=source_id,
            project_key=project_key,
            precondition_key=request.precondition_key,
            **PreconditionMapper._request_fields(request, identity, requested_at),
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
    def to_get_query(project_key: str, identifier) -> PreconditionQuery:
        return PreconditionQuery(project_key, identifier)

    @staticmethod
    def to_activate_command(
        project_key: str, identifier, reason: str | None
    ) -> ActivatePreconditionCommand:
        return ActivatePreconditionCommand(project_key, identifier, reason)

    @staticmethod
    def to_deprecate_command(
        project_key: str, identifier, reason: str | None
    ) -> DeprecatePreconditionCommand:
        return DeprecatePreconditionCommand(project_key, identifier, reason)

    @staticmethod
    def to_list_query(
        project_key: str, pagination: PaginationParams, status: VersionStatus | None
    ) -> ListPreconditionsQuery:
        return ListPreconditionsQuery(project_key, pagination, status)

    @staticmethod
    def to_versions_query(
        project_key: str,
        precondition_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None,
    ) -> PreconditionVersionsQuery:
        return PreconditionVersionsQuery(project_key, precondition_key, pagination, status)

    @staticmethod
    def to_api(precondition: Precondition, project_name: str) -> ApiPrecondition:
        return ApiPrecondition(
            id=precondition.identifier,
            project=ProjectReference(key=precondition.project_key, name=project_name),
            preconditionKey=precondition.precondition_key,
            version=precondition.version,
            name=precondition.name,
            description=precondition.description,
            validationDefinition=ApiDefinition(
                schemaVersion=precondition.validation_definition.schema_version,
                variables=dict(precondition.validation_definition.variables),
                actions=[
                    ApiAction(
                        id=action.identifier,
                        type=action.action_type,
                        source=action.source,
                        config=dict(action.configuration),
                    )
                    for action in precondition.validation_definition.actions
                ],
            ),
            status=precondition.status.value,
            createdAt=precondition.created_at,
            createdBy=precondition.created_by,
            metadata=dict(precondition.metadata or {}),
        )

    @staticmethod
    def to_list_response(
        page: Page[Precondition], project_name: str, pagination: PaginationParams
    ) -> PreconditionListResponse:
        return PreconditionListResponse(
            data=[PreconditionMapper.to_api(item, project_name) for item in page.items],
            pagination=ApiPagination(
                offset=pagination.offset,
                limit=pagination.limit,
                total=page.total,
            ),
        )

    @staticmethod
    def _request_fields(
        request: CreatePreconditionRequest, identity: str, requested_at: datetime
    ) -> dict:
        return {
            "name": request.name,
            "description": request.description,
            "validation_definition": PreconditionMapper._definition_to_domain(
                request.validation_definition
            ),
            "requested_by": identity,
            "requested_at": requested_at,
            "metadata": request.metadata,
        }

    @staticmethod
    def _definition_to_domain(definition: ApiDefinition) -> Definition:
        return Definition(
            schema_version=definition.schema_version,
            variables=definition.variables,
            actions=tuple(
                PreconditionMapper._action_to_domain(action) for action in definition.actions
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
