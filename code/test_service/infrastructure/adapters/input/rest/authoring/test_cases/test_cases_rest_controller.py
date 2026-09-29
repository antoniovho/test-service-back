"""Feature controller for Test Case Authoring operations."""

from datetime import UTC, datetime
from uuid import UUID

from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_test_case_request import CreateTestCaseRequest
from test_service_server.models.test_case import TestCase as ApiTestCase
from test_service_server.models.test_case_list_response import TestCaseListResponse
from test_service_server.models.test_case_version_list_response import TestCaseVersionListResponse

from test_service.bootstrap.container import get_injector
from test_service.domain.application.queries.projects import GetProjectQuery
from test_service.domain.ports.input.use_cases.authoring.test_cases.activate_test_case_use_case import (  # noqa: E501
    ActivateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.create_test_case_use_case import (  # noqa: E501
    CreateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.create_test_case_version_use_case import (  # noqa: E501
    CreateTestCaseVersionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.deprecate_test_case_use_case import (  # noqa: E501
    DeprecateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.get_test_case_use_case import (
    GetTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.list_test_case_versions_use_case import (  # noqa: E501
    ListTestCaseVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.list_test_cases_use_case import (  # noqa: E501
    ListTestCasesUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.infrastructure.adapters.input.rest.authoring.test_cases.test_case_mapper import (
    TestCaseMapper,
)
from test_service.infrastructure.adapters.input.rest.security.identity_context import (
    get_current_identity,
)


class TestCasesRestController:
    """Adapt Test Case use cases to the Authoring REST contract."""

    def __init__(self) -> None:
        injector = get_injector()
        self._create = injector.inject(CreateTestCaseUseCase)
        self._create_version = injector.inject(CreateTestCaseVersionUseCase)
        self._get = injector.inject(GetTestCaseUseCase)
        self._activate = injector.inject(ActivateTestCaseUseCase)
        self._deprecate = injector.inject(DeprecateTestCaseUseCase)
        self._list = injector.inject(ListTestCasesUseCase)
        self._list_versions = injector.inject(ListTestCaseVersionsUseCase)
        self._get_project = injector.inject(GetProjectUseCase)

    async def create(self, project_key: str, request: CreateTestCaseRequest) -> ApiTestCase:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestCaseMapper.to_create_command(
            project_key, request, get_current_identity(), datetime.now(UTC)
        )
        test_case = await self._create.execute(command)
        return TestCaseMapper.to_api(test_case, project.name)

    async def get(self, project_key: str, test_case_id: UUID) -> ApiTestCase:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        test_case = await self._get.execute(TestCaseMapper.to_get_query(project_key, test_case_id))
        return TestCaseMapper.to_api(test_case, project.name)

    async def create_version(
        self, project_key: str, test_case_id: UUID, request: CreateTestCaseRequest
    ) -> ApiTestCase:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestCaseMapper.to_create_version_command(
            project_key, test_case_id, request, get_current_identity(), datetime.now(UTC)
        )
        test_case = await self._create_version.execute(command)
        return TestCaseMapper.to_api(test_case, project.name)

    async def activate(
        self, project_key: str, test_case_id: UUID, request: ActionRequest | None
    ) -> ApiTestCase:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestCaseMapper.to_activate_command(
            project_key, test_case_id, request.reason if request else None
        )
        test_case = await self._activate.execute(command)
        return TestCaseMapper.to_api(test_case, project.name)

    async def deprecate(
        self, project_key: str, test_case_id: UUID, request: ActionRequest | None
    ) -> ApiTestCase:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        command = TestCaseMapper.to_deprecate_command(
            project_key, test_case_id, request.reason if request else None
        )
        test_case = await self._deprecate.execute(command)
        return TestCaseMapper.to_api(test_case, project.name)

    async def list(
        self,
        project_key: str,
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ) -> TestCaseListResponse:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        pagination = TestCaseMapper.to_pagination(offset, limit, sort_by, order)
        page = await self._list.execute(
            TestCaseMapper.to_list_query(project_key, pagination, TestCaseMapper.to_status(status))
        )
        return TestCaseMapper.to_list_response(page, project.name, pagination)

    async def list_versions(
        self,
        project_key: str,
        test_key: str,
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ) -> TestCaseVersionListResponse:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        pagination = TestCaseMapper.to_pagination(offset, limit, sort_by, order)
        page = await self._list_versions.execute(
            TestCaseMapper.to_versions_query(
                project_key, test_key, pagination, TestCaseMapper.to_status(status)
            )
        )
        return TestCaseMapper.to_version_list_response(page, project.name, pagination)
