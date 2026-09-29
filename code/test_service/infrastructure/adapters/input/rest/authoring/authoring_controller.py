"""Generated Authoring API controller delegation boundary."""

from uuid import UUID

from test_service_server.apis.authoring_api_base import BaseAuthoringApi
from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_test_case_request import CreateTestCaseRequest

from test_service.infrastructure.adapters.input.rest.authoring.test_cases.test_cases_rest_controller import (  # noqa: E501
    TestCasesRestController,
)


class AuthoringController(BaseAuthoringApi):
    """Delegate generated Authoring endpoints to their feature controllers."""

    def __init__(self) -> None:
        self._test_cases = TestCasesRestController()

    async def create_test_case(
        self,
        projectKey: str,  # NOSONAR
        create_test_case_request: CreateTestCaseRequest,  # NOSONAR
    ):
        return await self._test_cases.create(projectKey, create_test_case_request)

    async def get_test_case(self, projectKey: str, testCaseId: UUID):  # NOSONAR
        return await self._test_cases.get(projectKey, testCaseId)

    async def create_test_case_version(
        self,
        projectKey: str,  # NOSONAR
        testCaseId: UUID,  # NOSONAR
        create_test_case_request: CreateTestCaseRequest,  # NOSONAR
    ):
        return await self._test_cases.create_version(
            projectKey, testCaseId, create_test_case_request
        )

    async def activate_test_case(
        self,
        projectKey: str,  # NOSONAR
        testCaseId: UUID,  # NOSONAR
        action_request: ActionRequest | None,  # NOSONAR
    ):
        return await self._test_cases.activate(projectKey, testCaseId, action_request)

    async def deprecate_test_case(
        self,
        projectKey: str,  # NOSONAR
        testCaseId: UUID,  # NOSONAR
        action_request: ActionRequest | None,  # NOSONAR
    ):
        return await self._test_cases.deprecate(projectKey, testCaseId, action_request)

    async def list_test_cases(
        self,
        projectKey: str,  # NOSONAR
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ):
        return await self._test_cases.list(projectKey, status, offset, limit, sort_by, order)

    async def list_test_case_versions(
        self,
        projectKey: str,  # NOSONAR
        testKey: str,  # NOSONAR
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ):
        return await self._test_cases.list_versions(
            projectKey, testKey, status, offset, limit, sort_by, order
        )
