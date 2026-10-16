"""Use case implementation: restore a historical Test Plan."""

from uuid import uuid4

from test_service.domain.application.commands.composition import RestoreTestPlanCommand
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.invalid_lifecycle_transition_exception import (
    InvalidLifecycleTransitionException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.input.use_cases.composition.test_plans.restore_test_plan_use_case import (  # noqa: E501
    RestoreTestPlanUseCase,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (
    TestPlanPersistencePort,
)


class RestoreTestPlanUseCaseImpl(RestoreTestPlanUseCase):
    """Clone a deprecated Test Plan snapshot into the next draft version."""

    def __init__(
        self, repository: TestPlanPersistencePort, project_resolver: ProjectResolver
    ) -> None:
        self._repository = repository
        self._project_resolver = project_resolver

    async def execute(self, request: RestoreTestPlanCommand) -> TestPlan:
        await self._project_resolver.resolve_active(request.project_key)
        source = await self._repository.find_by_id(request.source_id)
        if source is None or source.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test plan", str(request.source_id), f"project '{request.project_key}'"
            )
        if source.status is not VersionStatus.DEPRECATED:
            raise InvalidLifecycleTransitionException(
                "only deprecated test plan snapshots can be restored"
            )
        latest = await self._repository.find_latest_version(source.project_key, source.plan_key)
        return await self._repository.save(
            TestPlan(
                identifier=uuid4(),
                project_key=source.project_key,
                plan_key=source.plan_key,
                version=(latest or source.version) + 1,
                name=source.name,
                execution_mode=source.execution_mode,
                timeout_seconds=source.timeout_seconds,
                created_at=request.requested_at,
                created_by=request.requested_by,
                test_set_ids=source.test_set_ids,
                test_case_ids=source.test_case_ids,
                exclusions=source.exclusions,
                description=source.description,
            )
        )
