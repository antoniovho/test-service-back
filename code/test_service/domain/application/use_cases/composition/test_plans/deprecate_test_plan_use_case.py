"""Use case implementation: deprecate Test Plan."""

from test_service.domain.application.commands.composition import DeprecateTestPlanCommand
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.composition.test_plans.deprecate_test_plan_use_case import (  # noqa: E501
    DeprecateTestPlanUseCase,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (
    TestPlanPersistencePort,
)


class DeprecateTestPlanUseCaseImpl(DeprecateTestPlanUseCase):
    """Deprecates one active Test Plan snapshot."""

    def __init__(self, test_plan_repository: TestPlanPersistencePort) -> None:
        self._test_plan_repository = test_plan_repository

    async def execute(self, request: DeprecateTestPlanCommand) -> TestPlan:
        """Transition the requested Test Plan snapshot to deprecated."""
        test_plan = await self._test_plan_repository.find_by_id(request.identifier)
        if test_plan is None or test_plan.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test plan", str(request.identifier), f"project '{request.project_key}'"
            )
        return await self._test_plan_repository.save(test_plan.deprecate())
