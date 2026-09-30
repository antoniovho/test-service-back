"""Mapping between generated Environment REST models and domain types."""

from datetime import datetime
from typing import Any
from uuid import UUID

from test_service_server.models.create_environment_request import CreateEnvironmentRequest
from test_service_server.models.environment import Environment as ApiEnvironment
from test_service_server.models.environment_list_response import EnvironmentListResponse
from test_service_server.models.pagination import Pagination as ApiPagination
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.application.commands.execution import (
    ActivateEnvironmentCommand,
    CreateEnvironmentCommand,
    DeactivateEnvironmentCommand,
)
from test_service.domain.application.queries.execution import (
    EnvironmentQuery,
    ListEnvironmentsQuery,
)
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.commons.pagination import SortOrder as DomainSortOrder
from test_service.domain.model.execution.environment import Environment, SecretReference


class EnvironmentMapper:
    """Translate between the Execution REST contract and Environment domain types."""

    @staticmethod
    def to_create_command(
        request: CreateEnvironmentRequest, requested_by: str, requested_at: datetime
    ) -> CreateEnvironmentCommand:
        return CreateEnvironmentCommand(
            environment_key=request.environment_key,
            name=request.name,
            requested_by=requested_by,
            requested_at=requested_at,
            description=request.description,
            configuration=EnvironmentMapper._to_domain_configuration(request.configuration),
        )

    @staticmethod
    def to_get_query(identifier: UUID) -> EnvironmentQuery:
        return EnvironmentQuery(identifier=identifier)

    @staticmethod
    def to_activate_command(identifier: UUID, reason: str | None) -> ActivateEnvironmentCommand:
        return ActivateEnvironmentCommand(identifier=identifier, reason=reason)

    @staticmethod
    def to_deactivate_command(identifier: UUID, reason: str | None) -> DeactivateEnvironmentCommand:
        return DeactivateEnvironmentCommand(identifier=identifier, reason=reason)

    @staticmethod
    def to_list_query(
        offset: int | None, limit: int | None, sort_by: str | None, order: ApiSortOrder | None
    ) -> ListEnvironmentsQuery:
        sort_fields = {
            "environmentKey": "environment_key",
            "name": "name",
            "createdAt": "created_at",
            "status": "status",
        }
        return ListEnvironmentsQuery(
            pagination=PaginationParams(
                offset=offset if offset is not None else 0,
                limit=limit if limit is not None else 20,
                sort_by=sort_fields.get(sort_by or "name", "name"),
                order=DomainSortOrder(order.value) if order is not None else DomainSortOrder.ASC,
            )
        )

    @staticmethod
    def to_api(environment: Environment) -> ApiEnvironment:
        return ApiEnvironment(
            id=environment.identifier,
            environmentKey=environment.environment_key,
            name=environment.name,
            description=environment.description,
            status=environment.status.value,
            configuration=EnvironmentMapper._to_api_configuration(environment.configuration),
            createdAt=environment.created_at,
            createdBy=environment.created_by,
        )

    @staticmethod
    def to_list_response(
        page: Page[Environment], pagination: PaginationParams
    ) -> EnvironmentListResponse:
        return EnvironmentListResponse(
            data=[EnvironmentMapper.to_api(environment) for environment in page.items],
            pagination=ApiPagination(
                offset=pagination.offset, limit=pagination.limit, total=page.total
            ),
        )

    @staticmethod
    def _to_domain_configuration(configuration: dict[str, Any] | None) -> dict[str, Any] | None:
        if configuration is None:
            return None
        return {
            key: (
                SecretReference(value["provider"], value["referenceKey"])
                if isinstance(value, dict) and set(value) == {"provider", "referenceKey"}
                else value
            )
            for key, value in configuration.items()
        }

    @staticmethod
    def _to_api_configuration(configuration) -> dict[str, Any] | None:
        if configuration is None:
            return None
        return {
            key: (
                {"provider": value.provider, "referenceKey": value.reference_key}
                if isinstance(value, SecretReference)
                else value
            )
            for key, value in configuration.items()
        }
