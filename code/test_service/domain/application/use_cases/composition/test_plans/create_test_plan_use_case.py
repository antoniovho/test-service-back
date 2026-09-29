"""Use case implementation: create Test Plan."""

from uuid import uuid4

from test_service.domain.application.commands.composition import CreateTestPlanCommand
from test_service.domain.application.services.test_case_snapshot_resolver import (
    TestCaseSnapshotResolver,
)
from test_service.domain.application.services.test_set_snapshot_resolver import (
    TestSetSnapshotResolver,
)
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.model.exceptions.test_plan_already_exists_exception import (
    TestPlanAlreadyExistsException,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.create_test_plan_use_case import (  # noqa: E501
    CreateTestPlanUseCase,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (
    TestPlanPersistencePort,
)


class CreateTestPlanUseCaseImpl(CreateTestPlanUseCase):
    """Creates the first draft snapshot of a Test Plan."""

    def __init__(
        self,
        test_plan_repository: TestPlanPersistencePort,
        test_set_snapshot_resolver: TestSetSnapshotResolver,
        test_case_snapshot_resolver: TestCaseSnapshotResolver,
    ) -> None:
        self._test_plan_repository = test_plan_repository
        self._test_set_snapshot_resolver = test_set_snapshot_resolver
        self._test_case_snapshot_resolver = test_case_snapshot_resolver

    async def execute(self, request: CreateTestPlanCommand) -> TestPlan:
        """Create and persist version one of a Test Plan."""
        latest_version = await self._test_plan_repository.find_latest_version(
            request.project_key, request.plan_key
        )
        if latest_version is not None:
            raise TestPlanAlreadyExistsException(request.project_key, request.plan_key)
        test_set_ids = await self._test_set_snapshot_resolver.resolve(
            request.project_key, request.test_set_ids
        )
        test_case_ids = await self._test_case_snapshot_resolver.resolve(
            request.project_key, request.test_case_ids
        )
        exclusions = await self._test_case_snapshot_resolver.resolve(
            request.project_key, request.exclusions
        )
        test_plan = TestPlan(
            identifier=uuid4(),
            project_key=request.project_key,
            plan_key=request.plan_key,
            version=1,
            name=request.name,
            execution_mode=request.execution_mode,
            timeout_seconds=request.timeout_seconds,
            created_at=request.requested_at,
            created_by=request.requested_by,
            test_set_ids=test_set_ids,
            test_case_ids=test_case_ids,
            exclusions=exclusions,
            description=request.description,
            max_parallelism=request.max_parallelism,
        )
        return await self._test_plan_repository.save(test_plan)
