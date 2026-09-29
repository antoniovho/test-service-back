"""Generated Composition API controller delegation boundary."""

from uuid import UUID

from test_service_server.apis.composition_api_base import BaseCompositionApi
from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_test_plan_request import CreateTestPlanRequest
from test_service_server.models.create_test_set_request import CreateTestSetRequest

from test_service.infrastructure.adapters.input.rest.composition.test_plans.test_plans_rest_controller import (  # noqa: E501
    TestPlansRestController,
)
from test_service.infrastructure.adapters.input.rest.composition.test_sets.test_sets_rest_controller import (  # noqa: E501
    TestSetsRestController,
)


class CompositionController(BaseCompositionApi):
    """Delegate generated Composition endpoints to their feature controllers."""

    def __init__(self) -> None:
        self._test_sets = TestSetsRestController()
        self._test_plans = TestPlansRestController()

    async def create_test_set(
        self,
        projectKey: str,  # NOSONAR
        create_test_set_request: CreateTestSetRequest,
    ):
        return await self._test_sets.create(projectKey, create_test_set_request)

    async def get_test_set(self, projectKey: str, testSetId: UUID):  # NOSONAR
        return await self._test_sets.get(projectKey, testSetId)

    async def create_test_set_version(
        self,
        projectKey: str,  # NOSONAR
        testSetId: UUID,  # NOSONAR
        create_test_set_request: CreateTestSetRequest,
    ):
        return await self._test_sets.create_version(projectKey, testSetId, create_test_set_request)

    async def activate_test_set(
        self,
        projectKey: str,  # NOSONAR
        testSetId: UUID,  # NOSONAR
        action_request: ActionRequest | None,
    ):
        return await self._test_sets.activate(projectKey, testSetId, action_request)

    async def deprecate_test_set(
        self,
        projectKey: str,  # NOSONAR
        testSetId: UUID,  # NOSONAR
        action_request: ActionRequest | None,
    ):
        return await self._test_sets.deprecate(projectKey, testSetId, action_request)

    async def list_test_sets(
        self,
        projectKey: str,  # NOSONAR
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ):
        return await self._test_sets.list(projectKey, status, offset, limit, sort_by, order)

    async def list_test_set_versions(
        self,
        projectKey: str,  # NOSONAR
        setKey: str,  # NOSONAR
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ):
        return await self._test_sets.list_versions(
            projectKey, setKey, status, offset, limit, sort_by, order
        )

    async def create_test_plan(
        self,
        projectKey: str,  # NOSONAR
        create_test_plan_request: CreateTestPlanRequest,  # NOSONAR
    ):
        return await self._test_plans.create(projectKey, create_test_plan_request)

    async def get_test_plan(self, projectKey: str, testPlanId: UUID):  # NOSONAR
        return await self._test_plans.get(projectKey, testPlanId)

    async def create_test_plan_version(
        self,
        projectKey: str,  # NOSONAR
        testPlanId: UUID,  # NOSONAR
        create_test_plan_request: CreateTestPlanRequest,
    ):  # NOSONAR
        return await self._test_plans.create_version(
            projectKey, testPlanId, create_test_plan_request
        )

    async def activate_test_plan(
        self,
        projectKey: str,  # NOSONAR
        testPlanId: UUID,  # NOSONAR
        action_request: ActionRequest | None,
    ):  # NOSONAR
        return await self._test_plans.activate(projectKey, testPlanId, action_request)

    async def deprecate_test_plan(
        self,
        projectKey: str,  # NOSONAR
        testPlanId: UUID,  # NOSONAR
        action_request: ActionRequest | None,
    ):  # NOSONAR
        return await self._test_plans.deprecate(projectKey, testPlanId, action_request)

    async def list_test_plans(
        self,
        projectKey: str,  # NOSONAR
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ):
        return await self._test_plans.list(projectKey, status, offset, limit, sort_by, order)

    async def list_test_plan_versions(
        self,
        projectKey: str,  # NOSONAR
        planKey: str,  # NOSONAR
        status: str | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ):
        return await self._test_plans.list_versions(
            projectKey, planKey, status, offset, limit, sort_by, order
        )
