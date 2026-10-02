"""Use case implementation: list Test Plans."""

from test_service.domain.application.queries.composition import ListTestPlansQuery
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import Page
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.ports.input.use_cases.composition.test_plans.list_test_plans_use_case import (  # noqa: E501
    ListTestPlansUseCase,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (
    TestPlanPersistencePort,
)


class ListTestPlansUseCaseImpl(ListTestPlansUseCase):
    """Lists Test Plan snapshots owned by one project."""

    def __init__(
        self, test_plan_repository: TestPlanPersistencePort, project_resolver: ProjectResolver
    ) -> None:
        self._test_plan_repository = test_plan_repository
        self._project_resolver = project_resolver

    async def execute(self, request: ListTestPlansQuery) -> Page[TestPlan]:
        """Return the requested project-scoped Test Plan page."""
        await self._project_resolver.resolve(request.project_key)
        return await self._test_plan_repository.find_page(
            request.project_key, request.pagination, request.status
        )
