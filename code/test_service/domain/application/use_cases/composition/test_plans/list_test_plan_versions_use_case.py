"""Use case implementation: list Test Plan versions."""

from test_service.domain.application.queries.composition import ListTestPlanVersionsQuery
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import Page
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.ports.input.use_cases.composition.test_plans.list_test_plan_versions_use_case import (  # noqa: E501
    ListTestPlanVersionsUseCase,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (
    TestPlanPersistencePort,
)


class ListTestPlanVersionsUseCaseImpl(ListTestPlanVersionsUseCase):
    """Lists Test Plan versions sharing one key."""

    def __init__(
        self, test_plan_repository: TestPlanPersistencePort, project_resolver: ProjectResolver
    ) -> None:
        self._test_plan_repository = test_plan_repository
        self._project_resolver = project_resolver

    async def execute(self, request: ListTestPlanVersionsQuery) -> Page[TestPlan]:
        """Return the requested project-scoped Test Plan version page."""
        await self._project_resolver.resolve(request.project_key)
        return await self._test_plan_repository.find_versions(
            request.project_key, request.plan_key, request.pagination, request.status
        )
