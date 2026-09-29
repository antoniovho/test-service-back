"""Use case implementation: get Test Plan."""

from test_service.domain.application.queries.composition import TestPlanQuery
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.composition.test_plans.get_test_plan_use_case import (  # noqa: E501
    GetTestPlanUseCase,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (  # noqa: E501
    TestPlanPersistencePort,
)


class GetTestPlanUseCaseImpl(GetTestPlanUseCase):
    """Retrieves one project-scoped Test Plan snapshot."""

    def __init__(self, test_plan_repository: TestPlanPersistencePort) -> None:
        self._test_plan_repository = test_plan_repository

    async def execute(self, request: TestPlanQuery) -> TestPlan:
        """Return a Test Plan only when it belongs to the requested project."""
        test_plan = await self._test_plan_repository.find_by_id(request.identifier)
        if test_plan is None or test_plan.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test plan", str(request.identifier), f"project '{request.project_key}'"
            )
        return test_plan
