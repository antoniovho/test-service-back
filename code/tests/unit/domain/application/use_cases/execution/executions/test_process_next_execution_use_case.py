import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.application.services.execution.definition_compiler import (
    DefinitionCompiler,
)
from test_service.domain.application.use_cases.execution.executions.process_next_execution_use_case import (  # noqa: E501
    ProcessNextExecutionUseCaseImpl,
)
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import (
    Priority,
    TestCase,
    TestLevel,
    TestType,
)
from test_service.domain.model.exceptions.execution_runner_unavailable_exception import (
    ExecutionRunnerUnavailableException,
)
from test_service.domain.model.execution.execution import (
    Execution,
    ExecutionStatus,
    ResultStatus,
    TriggerType,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.runners.runner_dtos import RunnerTestCaseOutcome

_STARTED_AT = datetime(2026, 1, 1, 10, tzinfo=UTC)
_FINISHED_AT = datetime(2026, 1, 1, 10, 0, 1, tzinfo=UTC)


def _test_case() -> TestCase:
    return TestCase(
        identifier=uuid4(),
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
        created_at=_STARTED_AT,
        created_by="author@example.test",
        status=VersionStatus.DEPRECATED,
    )


def _execution(
    test_case_id,
    runner_identifier: str = "runner",
    runner_version: str = "1.0",
) -> Execution:
    return Execution(
        identifier=uuid4(),
        project_key="IAG",
        test_plan_id=uuid4(),
        environment_id=uuid4(),
        trigger_type=TriggerType.API,
        created_at=_STARTED_AT,
        test_case_ids=(test_case_id,),
        runner_identifier=runner_identifier,
        runner_version=runner_version,
    ).start(_STARTED_AT)


class _Executions:
    def __init__(self, execution: Execution) -> None:
        self._execution = execution
        self.saved: list[Execution] = []

    async def claim_next_created(self) -> Execution | None:
        return self._execution

    async def save_execution(self, execution: Execution) -> Execution:
        self.saved.append(execution)
        return execution


class _Results:
    def __init__(self) -> None:
        self.saved = []

    async def save_results(self, result, actions, artifacts=()) -> None:
        self.saved.append((result, actions, artifacts))


class _TestCases:
    def __init__(self, test_case: TestCase) -> None:
        self._test_case = test_case

    async def find_by_id(self, identifier):
        return self._test_case if identifier == self._test_case.identifier else None


class _Preconditions:
    async def find_by_id(self, identifier):
        return None


class _Runner:
    def __init__(self, identifier: str = "runner", version: str = "1.0") -> None:
        self.identifier = identifier
        self.version = version
        self.executed_test_case_ids: list[str] = []

    def supports(self, action_types: frozenset[str]) -> bool:
        return True

    async def execute(self, test_case, cancellation: asyncio.Event) -> RunnerTestCaseOutcome:
        self.executed_test_case_ids.append(test_case.test_case_id)
        return RunnerTestCaseOutcome(
            status=ResultStatus.PASSED,
            started_at=_STARTED_AT,
            finished_at=_FINISHED_AT,
            actions=(),
        )


class _Cancellations:
    def __init__(self) -> None:
        self.registered = []
        self.unregistered = []

    def register(self, execution_id):
        self.registered.append(execution_id)
        return asyncio.Event()

    def unregister(self, execution_id) -> None:
        self.unregistered.append(execution_id)


class TestProcessNextExecutionUseCase:
    async def test_when_pinned_test_case_is_deprecated_expect_execution_uses_snapshot(self):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        executions = _Executions(execution)
        results = _Results()
        runner = _Runner()
        cancellations = _Cancellations()
        use_case = ProcessNextExecutionUseCaseImpl(
            executions,
            results,
            _TestCases(test_case),
            _Preconditions(),
            DefinitionCompiler(),
            runner,
            cancellations,
        )

        processed = await use_case.execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.PASSED
        assert runner.executed_test_case_ids == [str(test_case.identifier)]
        assert results.saved[0][0].test_case_id == test_case.identifier
        assert cancellations.unregistered == [execution.identifier]

    async def test_when_accepted_runner_is_unavailable_expect_contextual_error_log(self, caplog):
        test_case = _test_case()
        execution = _execution(test_case.identifier, "tavern", "2.4.1")
        runner = _Runner("other-runner", "1.0")
        use_case = ProcessNextExecutionUseCaseImpl(
            _Executions(execution),
            _Results(),
            _TestCases(test_case),
            _Preconditions(),
            DefinitionCompiler(),
            runner,
            _Cancellations(),
        )

        processed = await use_case.execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.ERROR
        assert str(execution.identifier) in caplog.text
        assert "tavern" in caplog.text
        assert "other-runner" in caplog.text
        assert isinstance(caplog.records[-1].exc_info[1], ExecutionRunnerUnavailableException)
