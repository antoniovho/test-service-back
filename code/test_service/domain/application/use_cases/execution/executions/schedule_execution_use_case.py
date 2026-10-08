"""Use case implementation: schedule a Test Plan execution."""

from uuid import uuid4

from test_service.domain.application.commands.execution import ScheduleExecutionCommand
from test_service.domain.application.services.resolvers.execution_manifest_resolver import (
    ExecutionManifestResolver,
)
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.invalid_environment_transition_exception import (
    InvalidEnvironmentTransitionException,
)
from test_service.domain.model.exceptions.invalid_test_plan_exception import (
    InvalidTestPlanException,
)
from test_service.domain.model.execution.environment import EnvironmentStatus
from test_service.domain.model.execution.execution import Execution
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.input.use_cases.execution.executions.schedule_execution_use_case import (  # noqa: E501
    ScheduleExecutionUseCase,
)
from test_service.domain.ports.output.persistence.environments.environment_persistence_port import (  # noqa: E501
    EnvironmentPersistencePort,
)
from test_service.domain.ports.output.persistence.executions.execution_persistence_port import (  # noqa: E501
    ExecutionPersistencePort,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (  # noqa: E501
    TestPlanPersistencePort,
)
from test_service.domain.ports.output.runners.runner_port import RunnerPort


class ScheduleExecutionUseCaseImpl(ScheduleExecutionUseCase):
    """Validates snapshots and persists a newly accepted execution."""

    def __init__(
        self,
        execution_repository: ExecutionPersistencePort,
        project_resolver: ProjectResolver,
        test_plan_repository: TestPlanPersistencePort,
        environment_repository: EnvironmentPersistencePort,
        manifest_resolver: ExecutionManifestResolver,
        runner: RunnerPort,
    ) -> None:
        self._execution_repository = execution_repository
        self._project_resolver = project_resolver
        self._test_plan_repository = test_plan_repository
        self._environment_repository = environment_repository
        self._manifest_resolver = manifest_resolver
        self._runner = runner

    async def execute(self, request: ScheduleExecutionCommand) -> Execution:
        """Accept an execution when its project, active plan, and environment are valid."""
        await self._project_resolver.resolve_active(request.project_key)
        test_plan = await self._test_plan_repository.find_by_id(request.test_plan_id)
        if test_plan is None or test_plan.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test plan", str(request.test_plan_id), f"project '{request.project_key}'"
            )
        if test_plan.status is not VersionStatus.ACTIVE:
            raise InvalidTestPlanException("only active test plan snapshots can be executed")
        environment = await self._environment_repository.find_by_id(request.environment_id)
        if environment is None:
            raise EntityNotFoundException("environment", str(request.environment_id))
        if environment.status is not EnvironmentStatus.ACTIVE:
            raise InvalidEnvironmentTransitionException("only active environments can be executed")
        test_case_ids = await self._manifest_resolver.resolve(test_plan, request.project_key)
        return await self._execution_repository.save_execution(
            Execution(
                identifier=uuid4(),
                project_key=request.project_key,
                test_plan_id=request.test_plan_id,
                environment_id=request.environment_id,
                trigger_type=request.trigger_type,
                created_at=request.requested_at,
                test_case_ids=test_case_ids,
                environment_snapshot=environment.configuration,
                triggered_by=request.triggered_by,
                runner_identifier=self._runner.identifier,
                runner_version=self._runner.version,
            )
        )
