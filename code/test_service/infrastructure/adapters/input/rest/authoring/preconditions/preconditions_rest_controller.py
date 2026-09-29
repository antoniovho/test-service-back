"""Feature controller for Precondition Authoring operations."""

from datetime import UTC, datetime
from uuid import UUID

from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_precondition_request import CreatePreconditionRequest
from test_service_server.models.precondition import Precondition as ApiPrecondition
from test_service_server.models.precondition_list_response import PreconditionListResponse

from test_service.bootstrap.container import get_injector
from test_service.domain.application.queries.projects import GetProjectQuery
from test_service.domain.ports.input.use_cases.authoring.preconditions.activate_precondition_use_case import (  # noqa: E501
    ActivatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.create_precondition_use_case import (  # noqa: E501
    CreatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.create_precondition_version_use_case import (  # noqa: E501
    CreatePreconditionVersionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.deprecate_precondition_use_case import (  # noqa: E501
    DeprecatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.get_precondition_use_case import (  # noqa: E501
    GetPreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.list_precondition_versions_use_case import (  # noqa: E501
    ListPreconditionVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.list_preconditions_use_case import (  # noqa: E501
    ListPreconditionsUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.infrastructure.adapters.input.rest.authoring.preconditions.precondition_mapper import (  # noqa: E501
    PreconditionMapper,
)
from test_service.infrastructure.adapters.input.rest.security.identity_context import (
    get_current_identity,
)


class PreconditionsRestController:
    """Adapt Precondition use cases to the Authoring REST contract."""

    def __init__(self) -> None:
        injector = get_injector()
        self._create = injector.inject(CreatePreconditionUseCase)
        self._create_version = injector.inject(CreatePreconditionVersionUseCase)
        self._get = injector.inject(GetPreconditionUseCase)
        self._activate = injector.inject(ActivatePreconditionUseCase)
        self._deprecate = injector.inject(DeprecatePreconditionUseCase)
        self._list = injector.inject(ListPreconditionsUseCase)
        self._list_versions = injector.inject(ListPreconditionVersionsUseCase)
        self._get_project = injector.inject(GetProjectUseCase)

    async def create(self, project_key: str, request: CreatePreconditionRequest) -> ApiPrecondition:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = PreconditionMapper.to_create_command(
            project_key, request, get_current_identity(), datetime.now(UTC)
        )
        precondition = await self._create.execute(command)
        return PreconditionMapper.to_api(precondition, project.name)

    async def get(self, project_key: str, precondition_id: UUID) -> ApiPrecondition:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        precondition = await self._get.execute(
            PreconditionMapper.to_get_query(project_key, precondition_id)
        )
        return PreconditionMapper.to_api(precondition, project.name)

    async def create_version(
        self, project_key: str, precondition_id: UUID, request: CreatePreconditionRequest
    ) -> ApiPrecondition:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = PreconditionMapper.to_create_version_command(
            project_key, precondition_id, request, get_current_identity(), datetime.now(UTC)
        )
        precondition = await self._create_version.execute(command)
        return PreconditionMapper.to_api(precondition, project.name)

    async def activate(
        self, project_key: str, precondition_id: UUID, request: ActionRequest | None
    ) -> ApiPrecondition:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = PreconditionMapper.to_activate_command(
            project_key, precondition_id, request.reason if request else None
        )
        precondition = await self._activate.execute(command)
        return PreconditionMapper.to_api(precondition, project.name)

    async def deprecate(
        self, project_key: str, precondition_id: UUID, request: ActionRequest | None
    ) -> ApiPrecondition:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = PreconditionMapper.to_deprecate_command(
            project_key, precondition_id, request.reason if request else None
        )
        precondition = await self._deprecate.execute(command)
        return PreconditionMapper.to_api(precondition, project.name)

    async def list(
        self,
        project_key: str,
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ) -> PreconditionListResponse:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        pagination = PreconditionMapper.to_pagination(offset, limit, sort_by, order)
        page = await self._list.execute(
            PreconditionMapper.to_list_query(
                project_key, pagination, PreconditionMapper.to_status(status)
            )
        )
        return PreconditionMapper.to_list_response(page, project.name, pagination)

    async def list_versions(
        self,
        project_key: str,
        precondition_key: str,
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ) -> PreconditionListResponse:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        pagination = PreconditionMapper.to_pagination(offset, limit, sort_by, order)
        page = await self._list_versions.execute(
            PreconditionMapper.to_versions_query(
                project_key, precondition_key, pagination, PreconditionMapper.to_status(status)
            )
        )
        return PreconditionMapper.to_list_response(page, project.name, pagination)
