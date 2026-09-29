"""Feature controller for Test Plan composition operations."""

from datetime import UTC, datetime
from uuid import UUID

from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_test_plan_request import CreateTestPlanRequest

from test_service.bootstrap.container import get_injector
from test_service.domain.application.queries.projects import GetProjectQuery
from test_service.domain.ports.input.use_cases.composition.test_plans.activate_test_plan_use_case import (  # noqa: E501
    ActivateTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.create_test_plan_use_case import (  # noqa: E501
    CreateTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.create_test_plan_version_use_case import (  # noqa: E501
    CreateTestPlanVersionUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.deprecate_test_plan_use_case import (  # noqa: E501
    DeprecateTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.get_test_plan_use_case import (  # noqa: E501
    GetTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.list_test_plan_versions_use_case import (  # noqa: E501  # noqa: E501
    ListTestPlanVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.list_test_plans_use_case import (  # noqa: E501
    ListTestPlansUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (  # noqa: E501
    GetProjectUseCase,
)
from test_service.infrastructure.adapters.input.rest.composition.test_plans.test_plan_mapper import (  # noqa: E501
    TestPlanMapper,
)
from test_service.infrastructure.adapters.input.rest.security.identity_context import (  # noqa: E501
    get_current_identity,
)


class TestPlansRestController:
    def __init__(self) -> None:
        injector = get_injector()
        self._create = injector.inject(CreateTestPlanUseCase)
        self._create_version = injector.inject(CreateTestPlanVersionUseCase)
        self._get = injector.inject(GetTestPlanUseCase)
        self._activate = injector.inject(ActivateTestPlanUseCase)
        self._deprecate = injector.inject(DeprecateTestPlanUseCase)
        self._list = injector.inject(ListTestPlansUseCase)
        self._list_versions = injector.inject(ListTestPlanVersionsUseCase)
        self._get_project = injector.inject(GetProjectUseCase)

    async def create(self, project_key: str, request: CreateTestPlanRequest):
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestPlanMapper.to_create_command(
            project_key, request, get_current_identity(), datetime.now(UTC)
        )
        result = await self._create.execute(command)
        return TestPlanMapper.to_api(result, project.name)

    async def get(self, project_key: str, test_plan_id: UUID):
        project = await self._get_project.execute(GetProjectQuery(project_key))
        test_plan = await self._get.execute(TestPlanMapper.to_get_query(project_key, test_plan_id))
        return TestPlanMapper.to_api(
            test_plan,
            project.name,
        )

    async def create_version(
        self, project_key: str, test_plan_id: UUID, request: CreateTestPlanRequest
    ):
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestPlanMapper.to_create_version_command(
            project_key, test_plan_id, request, get_current_identity(), datetime.now(UTC)
        )
        result = await self._create_version.execute(command)
        return TestPlanMapper.to_api(result, project.name)

    async def activate(self, project_key: str, test_plan_id: UUID, request: ActionRequest | None):
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestPlanMapper.to_activate_command(
            project_key, test_plan_id, request.reason if request else None
        )
        result = await self._activate.execute(command)
        return TestPlanMapper.to_api(result, project.name)

    async def deprecate(self, project_key: str, test_plan_id: UUID, request: ActionRequest | None):
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestPlanMapper.to_deprecate_command(
            project_key, test_plan_id, request.reason if request else None
        )
        result = await self._deprecate.execute(command)
        return TestPlanMapper.to_api(result, project.name)

    async def list(
        self,
        project_key: str,
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ):
        project = await self._get_project.execute(GetProjectQuery(project_key))
        pagination = TestPlanMapper.to_pagination(offset, limit, sort_by, order)
        page = await self._list.execute(
            TestPlanMapper.to_list_query(project_key, pagination, TestPlanMapper.to_status(status))
        )
        return TestPlanMapper.to_list_response(page, project.name, pagination)

    async def list_versions(
        self,
        project_key: str,
        plan_key: str,
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ):
        project = await self._get_project.execute(GetProjectQuery(project_key))
        pagination = TestPlanMapper.to_pagination(offset, limit, sort_by, order)
        page = await self._list_versions.execute(
            TestPlanMapper.to_versions_query(
                project_key, plan_key, pagination, TestPlanMapper.to_status(status)
            )
        )
        return TestPlanMapper.to_version_list_response(page, project.name, pagination)
