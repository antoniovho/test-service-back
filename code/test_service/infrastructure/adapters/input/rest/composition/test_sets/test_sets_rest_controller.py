"""Feature controller for Test Set composition operations."""

from datetime import UTC, datetime
from uuid import UUID

from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_test_set_request import CreateTestSetRequest
from test_service_server.models.test_set import TestSet as ApiTestSet
from test_service_server.models.test_set_list_response import TestSetListResponse
from test_service_server.models.test_set_version_list_response import TestSetVersionListResponse

from test_service.bootstrap.container import get_injector
from test_service.domain.application.queries.projects import GetProjectQuery
from test_service.domain.ports.input.use_cases.composition.test_sets.activate_test_set_use_case import (  # noqa: E501
    ActivateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.create_test_set_use_case import (  # noqa: E501
    CreateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.create_test_set_version_use_case import (  # noqa: E501
    CreateTestSetVersionUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.deprecate_test_set_use_case import (  # noqa: E501
    DeprecateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.get_test_set_use_case import (  # noqa: E501
    GetTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.list_test_set_versions_use_case import (  # noqa: E501
    ListTestSetVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.list_test_sets_use_case import (  # noqa: E501
    ListTestSetsUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.infrastructure.adapters.input.rest.composition.test_sets.test_set_mapper import (
    TestSetMapper,
)
from test_service.infrastructure.adapters.input.rest.security.identity_context import (
    get_current_identity,
)


class TestSetsRestController:
    """Adapt Test Set use cases to the Composition REST contract."""

    def __init__(self) -> None:
        injector = get_injector()
        self._create = injector.inject(CreateTestSetUseCase)
        self._create_version = injector.inject(CreateTestSetVersionUseCase)
        self._get = injector.inject(GetTestSetUseCase)
        self._activate = injector.inject(ActivateTestSetUseCase)
        self._deprecate = injector.inject(DeprecateTestSetUseCase)
        self._list = injector.inject(ListTestSetsUseCase)
        self._list_versions = injector.inject(ListTestSetVersionsUseCase)
        self._get_project = injector.inject(GetProjectUseCase)

    async def create(self, project_key: str, request: CreateTestSetRequest) -> ApiTestSet:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestSetMapper.to_create_command(
            project_key, request, get_current_identity(), datetime.now(UTC)
        )
        test_set = await self._create.execute(command)
        return TestSetMapper.to_api(test_set, project.name)

    async def get(self, project_key: str, test_set_id: UUID) -> ApiTestSet:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        test_set = await self._get.execute(TestSetMapper.to_get_query(project_key, test_set_id))
        return TestSetMapper.to_api(test_set, project.name)

    async def create_version(
        self, project_key: str, test_set_id: UUID, request: CreateTestSetRequest
    ) -> ApiTestSet:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestSetMapper.to_create_version_command(
            project_key, test_set_id, request, get_current_identity(), datetime.now(UTC)
        )
        test_set = await self._create_version.execute(command)
        return TestSetMapper.to_api(test_set, project.name)

    async def activate(
        self, project_key: str, test_set_id: UUID, request: ActionRequest | None
    ) -> ApiTestSet:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestSetMapper.to_activate_command(
            project_key, test_set_id, request.reason if request else None
        )
        test_set = await self._activate.execute(command)
        return TestSetMapper.to_api(test_set, project.name)

    async def deprecate(
        self, project_key: str, test_set_id: UUID, request: ActionRequest | None
    ) -> ApiTestSet:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestSetMapper.to_deprecate_command(
            project_key, test_set_id, request.reason if request else None
        )
        test_set = await self._deprecate.execute(command)
        return TestSetMapper.to_api(test_set, project.name)

    async def list(
        self,
        project_key: str,
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ) -> TestSetListResponse:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        pagination = TestSetMapper.to_pagination(offset, limit, sort_by, order)
        page = await self._list.execute(
            TestSetMapper.to_list_query(project_key, pagination, TestSetMapper.to_status(status))
        )
        return TestSetMapper.to_list_response(page, project.name, pagination)

    async def list_versions(
        self,
        project_key: str,
        set_key: str,
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ) -> TestSetVersionListResponse:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        pagination = TestSetMapper.to_pagination(offset, limit, sort_by, order)
        page = await self._list_versions.execute(
            TestSetMapper.to_versions_query(
                project_key, set_key, pagination, TestSetMapper.to_status(status)
            )
        )
        return TestSetMapper.to_version_list_response(page, project.name, pagination)
