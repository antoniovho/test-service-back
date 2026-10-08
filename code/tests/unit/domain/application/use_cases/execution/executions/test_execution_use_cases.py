from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from test_service.domain.application.commands.execution import (
    CancelExecutionCommand,
    ScheduleExecutionCommand,
)
from test_service.domain.application.queries.execution import ExecutionQuery, ListExecutionsQuery
from test_service.domain.application.services.execution.definition_compiler import (
    DefinitionCompiler,
)
from test_service.domain.application.services.resolvers.execution_access_resolver import (
    ExecutionAccessResolver,
)
from test_service.domain.application.services.resolvers.execution_manifest_resolver import (
    ExecutionManifestResolver,
)
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.application.use_cases.execution.executions.cancel_execution_use_case import (  # noqa: E501
    CancelExecutionUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.get_execution_use_case import (  # noqa: E501
    GetExecutionUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_executions_use_case import (  # noqa: E501
    ListExecutionsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.schedule_execution_use_case import (  # noqa: E501
    ScheduleExecutionUseCaseImpl,
)
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import (
    Priority,
    TestCase,
    TestLevel,
    TestType,
)
from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.invalid_environment_transition_exception import (
    InvalidEnvironmentTransitionException,
)
from test_service.domain.model.exceptions.invalid_test_plan_exception import (
    InvalidTestPlanException,
)
from test_service.domain.model.execution.environment import Environment, EnvironmentStatus
from test_service.domain.model.execution.execution import Execution, ExecutionStatus, TriggerType
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.model.projects.project import Project


def _execution(project_key: str = "IAG") -> Execution:
    return Execution(
        identifier=uuid4(),
        project_key=project_key,
        test_plan_id=uuid4(),
        environment_id=uuid4(),
        trigger_type=TriggerType.API,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _test_plan(
    project_key: str = "IAG",
    status: VersionStatus = VersionStatus.ACTIVE,
    test_set_ids: tuple = (),
    test_case_ids: tuple = (),
) -> TestPlan:
    return TestPlan(
        identifier=uuid4(),
        project_key=project_key,
        plan_key="checkout",
        version=1,
        name="Checkout",
        execution_mode=ExecutionMode.SEQUENTIAL,
        timeout_seconds=60,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        test_set_ids=test_set_ids,
        test_case_ids=test_case_ids,
        status=status,
    )


def _environment(
    status: EnvironmentStatus = EnvironmentStatus.ACTIVE,
    configuration=None,
) -> Environment:
    return Environment(
        identifier=uuid4(),
        environment_key="staging-eu",
        name="Staging Europe",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        configuration=configuration,
        status=status,
    )


def _test_case(identifier=None) -> TestCase:
    return TestCase(
        identifier=identifier or uuid4(),
        project_key="IAG",
        test_key="checkout",
        version=1,
        name="Checkout",
        summary="Checks checkout",
        objective="Complete checkout",
        test_type=TestType.AUTOMATED,
        test_level=TestLevel.FUNCTIONAL,
        priority=Priority.HIGH,
        definition=Definition(
            variables={},
            actions=(Action("request", "HTTP", {"url": "https://example.test"}),),
        ),
        timeout_seconds=60,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        status=VersionStatus.ACTIVE,
    )


def _project() -> Project:
    return Project(
        key="IAG",
        name="Test project",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
    )


class _ExecutionRepository:
    def __init__(self, execution: Execution | None = None) -> None:
        self.execution = execution
        self.saved: Execution | None = None

    async def save_execution(self, execution: Execution) -> Execution:
        self.saved = execution
        return execution

    async def find_execution(self, identifier):
        return self.execution

    async def find_page(self, project_key: str, pagination):
        return Page((), 0) if self.execution is None else Page((self.execution,), 1)


class _ProjectRepository:
    def __init__(self, project: Project | None) -> None:
        self._project = project

    async def save(self, project: Project) -> Project:
        return project

    async def find_by_key(self, key: str) -> Project | None:
        return self._project

    async def find_page(self, pagination: PaginationParams) -> Page[Project]:
        return Page((), 0) if self._project is None else Page((self._project,), 1)


class _CancellationRegistry:
    def __init__(self) -> None:
        self.cancelled = []

    def request_cancellation(self, execution_id) -> None:
        self.cancelled.append(execution_id)


class TestExecutionUseCases:
    async def test_when_dependencies_are_valid_expect_created_execution_saved(self):
        test_plan = _test_plan()
        environment = _environment()
        execution_repository = _ExecutionRepository()
        use_case = _schedule_use_case(execution_repository, test_plan, environment)
        command = ScheduleExecutionCommand(
            project_key="IAG",
            test_plan_id=test_plan.identifier,
            environment_id=environment.identifier,
            trigger_type=TriggerType.API,
            requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        execution = await use_case.execute(command)

        assert execution.status is ExecutionStatus.CREATED
        assert execution_repository.saved == execution
        assert execution.test_case_ids == ()
        assert execution.runner_identifier == "runner"
        assert execution.runner_version == "1.0"

    async def test_when_composition_is_valid_expect_effective_snapshots_are_persisted(self):
        test_case = _test_case()
        test_plan = _test_plan(test_case_ids=(test_case.identifier,))
        environment = _environment(configuration={"baseUrl": "https://staging.example.test"})
        repository = _ExecutionRepository()
        use_case = _schedule_use_case(repository, test_plan, environment, test_case=test_case)
        command = ScheduleExecutionCommand(
            project_key="IAG",
            test_plan_id=test_plan.identifier,
            environment_id=environment.identifier,
            trigger_type=TriggerType.API,
            requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        execution = await use_case.execute(command)

        assert execution.test_case_ids == (test_case.identifier,)
        assert execution.environment_snapshot == environment.configuration
        assert repository.saved == execution

    async def test_when_test_set_is_unavailable_expect_rejection_with_identifier(self):
        test_set_id = uuid4()
        test_plan = _test_plan(test_set_ids=(test_set_id,))
        environment = _environment()
        repository = _ExecutionRepository()
        use_case = _schedule_use_case(repository, test_plan, environment)
        command = ScheduleExecutionCommand(
            project_key="IAG",
            test_plan_id=test_plan.identifier,
            environment_id=environment.identifier,
            trigger_type=TriggerType.API,
            requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        with pytest.raises(InvalidTestPlanException, match=str(test_set_id)):
            await use_case.execute(command)

        assert repository.saved is None

    async def test_when_test_case_is_unavailable_expect_rejection_with_identifier(self):
        test_case_id = uuid4()
        test_plan = _test_plan(test_case_ids=(test_case_id,))
        environment = _environment()
        repository = _ExecutionRepository()
        use_case = _schedule_use_case(repository, test_plan, environment)
        command = ScheduleExecutionCommand(
            project_key="IAG",
            test_plan_id=test_plan.identifier,
            environment_id=environment.identifier,
            trigger_type=TriggerType.API,
            requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        with pytest.raises(InvalidTestPlanException, match=str(test_case_id)):
            await use_case.execute(command)

        assert repository.saved is None

    @pytest.mark.parametrize(
        ("project", "plan", "environment", "exception"),
        [
            (None, None, None, EntityNotFoundException),
            (_project(), None, None, EntityNotFoundException),
            (_project(), _test_plan("ZAR"), None, EntityNotFoundException),
            (
                _project(),
                _test_plan(status=VersionStatus.DRAFT),
                None,
                InvalidTestPlanException,
            ),
            (_project(), _test_plan(), None, EntityNotFoundException),
            (
                _project(),
                _test_plan(),
                _environment(EnvironmentStatus.INACTIVE),
                InvalidEnvironmentTransitionException,
            ),
        ],
        ids=[
            "missing-project",
            "missing-plan",
            "foreign-plan",
            "draft-plan",
            "missing-environment",
            "inactive-environment",
        ],
    )
    async def test_when_dependencies_are_invalid_expect_rejection(
        self, project, plan, environment, exception
    ):
        command = ScheduleExecutionCommand(
            project_key="IAG",
            test_plan_id=uuid4(),
            environment_id=uuid4(),
            trigger_type=TriggerType.API,
            requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        use_case = _schedule_use_case(_ExecutionRepository(), plan, environment, project)

        with pytest.raises(exception):
            await use_case.execute(command)

    async def test_when_execution_belongs_to_project_expect_retrieved(self):
        execution = _execution()
        query = ExecutionQuery("IAG", execution.identifier)

        result = await GetExecutionUseCaseImpl(
            ExecutionAccessResolver(_ExecutionRepository(execution))
        ).execute(query)

        assert result == execution

    async def test_when_execution_is_foreign_expect_not_found(self):
        execution = _execution("ZAR")
        query = ExecutionQuery("IAG", execution.identifier)
        use_case = GetExecutionUseCaseImpl(ExecutionAccessResolver(_ExecutionRepository(execution)))

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(query)

    async def test_when_project_exists_expect_execution_page(self):
        execution = _execution()
        query = ListExecutionsQuery("IAG", PaginationParams())
        use_case = ListExecutionsUseCaseImpl(
            _ExecutionRepository(execution),
            _project_resolver(_project()),
        )

        page = await use_case.execute(query)

        assert page.items == (execution,)

    async def test_when_project_is_missing_expect_execution_list_not_found(self):
        query = ListExecutionsQuery("IAG", PaginationParams())
        use_case = ListExecutionsUseCaseImpl(_ExecutionRepository(), _project_resolver(None))

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(query)

    async def test_when_execution_belongs_to_project_expect_cancelled_snapshot_saved(self):
        execution = _execution()
        command = CancelExecutionCommand("IAG", execution.identifier)
        repository = _ExecutionRepository(execution)
        cancellation = _CancellationRegistry()

        result = await CancelExecutionUseCaseImpl(repository, cancellation).execute(command)

        assert result.status is ExecutionStatus.CANCELLED
        assert repository.saved == result
        assert cancellation.cancelled == [execution.identifier]

    async def test_when_cancelling_foreign_execution_expect_not_found(self):
        execution = _execution("ZAR")
        command = CancelExecutionCommand("IAG", execution.identifier)
        use_case = CancelExecutionUseCaseImpl(
            _ExecutionRepository(execution), _CancellationRegistry()
        )

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(command)


async def _async_result(value):
    return value


def _project_resolver(project: Project | None) -> ProjectResolver:
    return ProjectResolver(_ProjectRepository(project))


def _schedule_use_case(
    execution_repository,
    test_plan,
    environment,
    project: Project | None = None,
    test_case: TestCase | None = None,
):
    if project is None:
        project = _project()
    missing_snapshot_repository = SimpleNamespace(find_by_id=lambda identifier: _async_result(None))
    test_case_repository = SimpleNamespace(find_by_id=lambda identifier: _async_result(test_case))
    runner = SimpleNamespace(identifier="runner", version="1.0", supports=lambda action_types: True)
    return ScheduleExecutionUseCaseImpl(
        execution_repository,
        _project_resolver(project),
        SimpleNamespace(find_by_id=lambda identifier: _async_result(test_plan)),
        SimpleNamespace(find_by_id=lambda identifier: _async_result(environment)),
        ExecutionManifestResolver(
            missing_snapshot_repository,
            test_case_repository,
            missing_snapshot_repository,
            DefinitionCompiler(),
            runner,
        ),
        runner,
    )
