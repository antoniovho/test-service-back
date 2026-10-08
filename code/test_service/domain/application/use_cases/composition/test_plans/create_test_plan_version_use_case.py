"""Use case implementation: create Test Plan version."""

from uuid import uuid4

from test_service.domain.application.commands.composition import CreateTestPlanVersionCommand
from test_service.domain.application.services.resolvers.test_case_snapshot_resolver import (
    TestCaseSnapshotResolver,
)
from test_service.domain.application.services.resolvers.test_set_snapshot_resolver import (
    TestSetSnapshotResolver,
)
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.composition.test_plans.create_test_plan_version_use_case import (  # noqa: E501
    CreateTestPlanVersionUseCase,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (
    TestPlanPersistencePort,
)


class CreateTestPlanVersionUseCaseImpl(CreateTestPlanVersionUseCase):
    """Creates a new draft snapshot from an existing Test Plan snapshot."""

    def __init__(
        self,
        test_plan_repository: TestPlanPersistencePort,
        test_set_snapshot_resolver: TestSetSnapshotResolver,
        test_case_snapshot_resolver: TestCaseSnapshotResolver,
    ) -> None:
        self._test_plan_repository = test_plan_repository
        self._test_set_snapshot_resolver = test_set_snapshot_resolver
        self._test_case_snapshot_resolver = test_case_snapshot_resolver

    async def execute(self, request: CreateTestPlanVersionCommand) -> TestPlan:
        """Create and persist the next immutable Test Plan version."""
        source = await self._test_plan_repository.find_by_id(request.source_id)
        if source is None or source.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test plan", str(request.source_id), f"project '{request.project_key}'"
            )
        latest_version = await self._test_plan_repository.find_latest_version(
            source.project_key, source.plan_key
        )
        test_set_ids = await self._test_set_snapshot_resolver.resolve(
            source.project_key, request.test_set_ids
        )
        test_case_ids = await self._test_case_snapshot_resolver.resolve(
            source.project_key, request.test_case_ids
        )
        exclusions = await self._test_case_snapshot_resolver.resolve(
            source.project_key, request.exclusions
        )
        test_plan = TestPlan(
            identifier=uuid4(),
            project_key=source.project_key,
            plan_key=source.plan_key,
            version=(latest_version or source.version) + 1,
            name=request.name,
            execution_mode=request.execution_mode,
            timeout_seconds=request.timeout_seconds,
            created_at=request.requested_at,
            created_by=request.requested_by,
            test_set_ids=test_set_ids,
            test_case_ids=test_case_ids,
            exclusions=exclusions,
            description=request.description,
        )
        return await self._test_plan_repository.save(test_plan)
