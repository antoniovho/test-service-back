import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.application.services.execution.definition_compiler import (
    DefinitionCompiler,
)
from test_service.domain.application.services.execution.execution_variables_resolver import (
    ExecutionVariablesResolver,
)
from test_service.domain.application.use_cases.execution.executions import (
    process_next_execution_use_case,
)
from test_service.domain.application.use_cases.execution.executions.process_next_execution_use_case import (  # noqa: E501
    ProcessNextExecutionUseCaseImpl,
)
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.authoring.test_case import (
    PreconditionReference,
    TestCase,
)
from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.execution_runner_unavailable_exception import (
    ExecutionRunnerUnavailableException,
)
from test_service.domain.model.exceptions.secret_resolution_exception import (
    SecretResolutionException,
)
from test_service.domain.model.execution.environment import SecretReference
from test_service.domain.model.execution.execution import (
    Execution,
    ExecutionStatus,
    ResultStatus,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.runners.runner_dtos import (
    RunnerActionOutcome,
    RunnerTestCaseOutcome,
)
from tests.mothers.execution_mother import a_test_case, an_execution

_STARTED_AT = datetime(2026, 1, 1, 10, tzinfo=UTC)
_FINISHED_AT = datetime(2026, 1, 1, 10, 0, 1, tzinfo=UTC)


def _test_case(
    variables: dict[str, str] | None = None,
    timeout_seconds: int = 60,
    preconditions: tuple[PreconditionReference, ...] = (),
) -> TestCase:
    return a_test_case(
        variables=variables,
        timeout_seconds=timeout_seconds,
        preconditions=preconditions,
        created_at=_STARTED_AT,
        status=VersionStatus.DEPRECATED,
    )


def _test_plan(timeout_seconds: int = 3600) -> TestPlan:
    return TestPlan(
        identifier=uuid4(),
        project_key="IAG",
        plan_key="smoke",
        version=1,
        name="Smoke",
        execution_mode=ExecutionMode.SEQUENTIAL,
        timeout_seconds=timeout_seconds,
        created_at=_STARTED_AT,
        created_by="author@example.test",
        status=VersionStatus.ACTIVE,
    )


def _execution(
    test_case_id,
    runner_identifier: str = "runner",
    runner_version: str = "1.0",
    environment_snapshot: dict[str, object] | None = None,
) -> Execution:
    return an_execution(
        test_case_ids=(test_case_id,),
        environment_snapshot=environment_snapshot,
        runner_identifier=runner_identifier,
        runner_version=runner_version,
        created_at=_STARTED_AT,
    ).start(_STARTED_AT)


class _Executions:
    def __init__(self, execution: Execution) -> None:
        self._execution = execution
        self.current = execution
        self.saved: list[Execution] = []
        self.transitions: list[tuple[Execution, tuple[ExecutionStatus, ...]]] = []
        self.recovery_calls = 0
        self.calls: list[str] = []

    async def claim_next_created(self) -> Execution | None:
        self.calls.append("claim")
        return self._execution

    async def recover_stale_running(self) -> int:
        self.recovery_calls += 1
        self.calls.append("recover")
        return 0

    async def find_execution(self, identifier):
        return self.current

    async def save_execution(self, execution: Execution) -> Execution:
        self.saved.append(execution)
        return execution

    async def transition_execution(self, execution, expected_statuses):
        self.transitions.append((execution, expected_statuses))
        if self.current.status in expected_statuses:
            self.current = execution
            self.saved.append(execution)
        return self.current


class _Results:
    def __init__(self) -> None:
        self.saved = []

    async def save_results(self, result, actions, artifacts=()) -> None:
        self.saved.append((result, actions, artifacts))


class _TestCases:
    def __init__(self, *test_cases: TestCase) -> None:
        self._test_cases = {test_case.identifier: test_case for test_case in test_cases}

    async def find_by_id(self, identifier):
        return self._test_cases.get(identifier)


class _TestPlans:
    def __init__(self, test_plan: TestPlan | None) -> None:
        self._test_plan = test_plan

    async def find_by_id(self, identifier):
        return self._test_plan


class _Preconditions:
    def __init__(self, *preconditions: Precondition) -> None:
        self._preconditions = {item.identifier: item for item in preconditions}

    async def find_by_id(self, identifier):
        return self._preconditions.get(identifier)


class _Runner:
    def __init__(
        self,
        identifier: str = "runner",
        version: str = "1.0",
        outcome: RunnerTestCaseOutcome | None = None,
    ) -> None:
        self.identifier = identifier
        self.version = version
        self.executed_test_case_ids: list[str] = []
        self.executed_variables: list[dict[str, str]] = []
        self._outcome = outcome or RunnerTestCaseOutcome(
            status=ResultStatus.PASSED,
            started_at=_STARTED_AT,
            finished_at=_FINISHED_AT,
            actions=(),
        )

    def supports(self, action_types: frozenset[str]) -> bool:
        return True

    async def execute(self, test_case, cancellation: asyncio.Event) -> RunnerTestCaseOutcome:
        self.executed_test_case_ids.append(test_case.test_case_id)
        self.executed_variables.append(dict(test_case.variables))
        return self._outcome


class _SequenceRunner(_Runner):
    def __init__(self, *outcomes: RunnerTestCaseOutcome) -> None:
        super().__init__()
        self._outcomes = list(outcomes)

    async def execute(self, test_case, cancellation: asyncio.Event) -> RunnerTestCaseOutcome:
        self.executed_test_case_ids.append(test_case.test_case_id)
        self.executed_variables.append(dict(test_case.variables))
        return self._outcomes.pop(0)


class _ConcurrentCancellationRunner(_Runner):
    def __init__(self, executions: _Executions) -> None:
        super().__init__()
        self._executions = executions

    async def execute(self, test_case, cancellation: asyncio.Event) -> RunnerTestCaseOutcome:
        self._executions.current = self._executions.current.cancel(_FINISHED_AT)
        return await super().execute(test_case, cancellation)


class _WaitingForCancellationRunner(_Runner):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()

    async def execute(self, test_case, cancellation: asyncio.Event) -> RunnerTestCaseOutcome:
        self.started.set()
        await cancellation.wait()
        return RunnerTestCaseOutcome(
            status=ResultStatus.SKIPPED,
            started_at=_STARTED_AT,
            finished_at=_FINISHED_AT,
            actions=(),
            error_code="CANCELLED",
        )


class _HangingRunner(_Runner):
    """Runner whose first calls never finish on their own, like a stuck request."""

    def __init__(self, hanging_calls: int = 1) -> None:
        super().__init__()
        self.calls = 0
        self._hanging_calls = hanging_calls

    async def execute(self, test_case, cancellation: asyncio.Event) -> RunnerTestCaseOutcome:
        self.calls += 1
        if self.calls <= self._hanging_calls:
            await asyncio.Event().wait()
        return await super().execute(test_case, cancellation)


class _SecretResolver:
    def __init__(self, values: dict[str, str] | None = None) -> None:
        self._values = values or {}

    async def resolve_secret(self, reference: SecretReference) -> str:
        if reference.reference_key not in self._values:
            raise SecretResolutionException("secret is not available")
        return self._values[reference.reference_key]


class _Cancellations:
    def __init__(self) -> None:
        self.registered = []
        self.unregistered = []

    def register(self, execution_id):
        self.registered.append(execution_id)
        return asyncio.Event()

    def unregister(self, execution_id) -> None:
        self.unregistered.append(execution_id)


def _use_case(
    execution: Execution,
    test_case: TestCase,
    runner: _Runner,
    results: _Results | None = None,
    secrets: dict[str, str] | None = None,
    test_plans: _TestPlans | None = None,
    other_test_cases: tuple[TestCase, ...] = (),
    preconditions: tuple[Precondition, ...] = (),
) -> ProcessNextExecutionUseCaseImpl:
    return ProcessNextExecutionUseCaseImpl(
        _Executions(execution),
        results or _Results(),
        _TestCases(test_case, *other_test_cases),
        _Preconditions(*preconditions),
        test_plans or _TestPlans(_test_plan()),
        DefinitionCompiler(),
        runner,
        _Cancellations(),
        ExecutionVariablesResolver(_SecretResolver(secrets)),
    )


class TestProcessNextExecutionUseCase:
    async def test_when_processing_next_execution_expect_stale_executions_recovered_first(self):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        executions = _Executions(execution)
        use_case = ProcessNextExecutionUseCaseImpl(
            executions,
            _Results(),
            _TestCases(test_case),
            _Preconditions(),
            _TestPlans(_test_plan()),
            DefinitionCompiler(),
            _Runner(),
            _Cancellations(),
            ExecutionVariablesResolver(_SecretResolver()),
        )

        await use_case.execute(None)

        assert executions.recovery_calls == 1
        assert executions.calls[:2] == ["recover", "claim"]

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
            _TestPlans(_test_plan()),
            DefinitionCompiler(),
            runner,
            cancellations,
            ExecutionVariablesResolver(_SecretResolver()),
        )

        processed = await use_case.execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.PASSED
        assert runner.executed_test_case_ids == [str(test_case.identifier)]
        assert results.saved[0][0].test_case_id == test_case.identifier
        assert cancellations.unregistered == [execution.identifier]

    async def test_when_precondition_saves_variables_expect_saved_evidence_and_variables_forwarded(
        self,
    ):
        precondition_id = uuid4()
        reference = PreconditionReference(precondition_id, "authenticated", 1)
        test_case = _test_case(preconditions=(reference,))
        precondition = Precondition(
            identifier=precondition_id,
            project_key="IAG",
            precondition_key="authenticated",
            version=1,
            name="Authenticated session",
            description="Creates an authenticated session",
            validation_definition=Definition(
                variables={},
                actions=(Action("login", "HTTP", {"url": "https://example.test/login"}),),
            ),
            created_at=_STARTED_AT,
            created_by="author@example.test",
            status=VersionStatus.ACTIVE,
        )
        precondition_outcome = RunnerTestCaseOutcome(
            status=ResultStatus.PASSED,
            started_at=_STARTED_AT,
            finished_at=_FINISHED_AT,
            actions=(
                RunnerActionOutcome(
                    "login",
                    "HTTP",
                    ResultStatus.PASSED,
                    _STARTED_AT,
                    _FINISHED_AT,
                    actual={"statusCode": 200},
                ),
            ),
            variables={"sessionToken": "temporary-token"},
        )
        runner = _SequenceRunner(precondition_outcome, _Runner()._outcome)
        results = _Results()
        execution = _execution(test_case.identifier)

        processed = await _use_case(
            execution, test_case, runner, results, preconditions=(precondition,)
        ).execute(None)

        assert processed is not None
        assert runner.executed_variables == [{}, {"sessionToken": "temporary-token"}]
        result, actions, _ = results.saved[0]
        assert result.status is ResultStatus.PASSED
        assert actions[0].action_id == f"precondition:{precondition_id}"
        assert actions[0].action_type == "PRECONDITION"
        assert actions[0].status is ResultStatus.PASSED
        assert actions[1].action_id == f"precondition:{precondition_id}:login"
        assert "temporary-token" not in repr(results.saved)

    async def test_when_precondition_fails_expect_blocked_result_with_precondition_evidence(
        self,
    ):
        precondition_id = uuid4()
        reference = PreconditionReference(precondition_id, "authenticated", 1)
        test_case = _test_case(preconditions=(reference,))
        precondition = Precondition(
            identifier=precondition_id,
            project_key="IAG",
            precondition_key="authenticated",
            version=1,
            name="Authenticated session",
            description="Creates an authenticated session",
            validation_definition=Definition(
                variables={},
                actions=(Action("login", "HTTP", {"url": "https://example.test/login"}),),
            ),
            created_at=_STARTED_AT,
            created_by="author@example.test",
            status=VersionStatus.ACTIVE,
        )
        failure = RunnerTestCaseOutcome(
            status=ResultStatus.FAILED,
            started_at=_STARTED_AT,
            finished_at=_FINISHED_AT,
            actions=(
                RunnerActionOutcome(
                    "login",
                    "HTTP",
                    ResultStatus.FAILED,
                    _STARTED_AT,
                    _FINISHED_AT,
                    error_code="TAVERN_ASSERTION_FAILED",
                ),
            ),
            error_code="TAVERN_ASSERTION_FAILED",
        )
        runner = _SequenceRunner(failure)
        results = _Results()

        await _use_case(
            _execution(test_case.identifier),
            test_case,
            runner,
            results,
            preconditions=(precondition,),
        ).execute(None)

        result, actions, _ = results.saved[0]
        assert result.status is ResultStatus.BLOCKED
        assert result.error_code == "PRECONDITION_FAILED"
        assert runner.executed_test_case_ids == [str(precondition_id)]
        assert actions[0].action_id == f"precondition:{precondition_id}"
        assert actions[0].status is ResultStatus.FAILED

    async def test_when_cancel_wins_during_runner_expect_worker_preserves_cancelled_state(self):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        executions = _Executions(execution)
        use_case = ProcessNextExecutionUseCaseImpl(
            executions,
            _Results(),
            _TestCases(test_case),
            _Preconditions(),
            _TestPlans(_test_plan()),
            DefinitionCompiler(),
            _ConcurrentCancellationRunner(executions),
            _Cancellations(),
            ExecutionVariablesResolver(_SecretResolver()),
        )

        processed = await use_case.execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.CANCELLED
        assert executions.current.status is ExecutionStatus.CANCELLED
        assert executions.transitions[0][1] == (ExecutionStatus.RUNNING,)

    async def test_when_cancel_is_persisted_by_another_replica_expect_running_runner_stopped(
        self,
    ):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        executions = _Executions(execution)
        runner = _WaitingForCancellationRunner()
        use_case = ProcessNextExecutionUseCaseImpl(
            executions,
            _Results(),
            _TestCases(test_case),
            _Preconditions(),
            _TestPlans(_test_plan()),
            DefinitionCompiler(),
            runner,
            _Cancellations(),
            ExecutionVariablesResolver(_SecretResolver()),
        )
        processing = asyncio.create_task(use_case.execute(None))

        await runner.started.wait()
        executions.current = executions.current.cancel(_FINISHED_AT)
        processed = await asyncio.wait_for(processing, timeout=1)

        assert processed is not None
        assert processed.status is ExecutionStatus.CANCELLED
        assert executions.current.status is ExecutionStatus.CANCELLED

    async def test_when_poll_recovers_after_db_error_expect_remote_cancel_observed(
        self, monkeypatch, caplog
    ):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        executions = _Executions(execution)
        calls = 0

        async def find_execution(identifier):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("temporary database failure")
            executions.current = executions.current.cancel(_FINISHED_AT)
            return executions.current

        async def skip_poll_interval(interval):
            return None

        monkeypatch.setattr(executions, "find_execution", find_execution)
        monkeypatch.setattr(process_next_execution_use_case.asyncio, "sleep", skip_poll_interval)
        use_case = ProcessNextExecutionUseCaseImpl(
            executions,
            _Results(),
            _TestCases(test_case),
            _Preconditions(),
            _TestPlans(_test_plan()),
            DefinitionCompiler(),
            _Runner(),
            _Cancellations(),
            ExecutionVariablesResolver(_SecretResolver()),
        )
        cancellation = asyncio.Event()

        await use_case._watch_persisted_cancellation(execution.identifier, cancellation)

        assert cancellation.is_set()
        assert calls == 2
        assert caplog.text.count("Failed to poll persisted cancellation") == 1

    async def test_when_accepted_runner_is_unavailable_expect_contextual_error_log(self, caplog):
        test_case = _test_case()
        execution = _execution(test_case.identifier, "tavern", "2.4.1")
        runner = _Runner("other-runner", "1.0")
        use_case = _use_case(execution, test_case, runner)

        processed = await use_case.execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.ERROR
        assert str(execution.identifier) in caplog.text
        assert "tavern" in caplog.text
        assert "other-runner" in caplog.text
        assert isinstance(caplog.records[-1].exc_info[1], ExecutionRunnerUnavailableException)

    async def test_when_environment_defines_variables_expect_runner_receives_them_first(self):
        test_case = _test_case({"baseUrl": "https://definition.test", "tenant": "acme"})
        execution = _execution(
            test_case.identifier,
            environment_snapshot={"baseUrl": "https://env.test", "retries": 3, "verbose": True},
        )
        runner = _Runner()
        use_case = _use_case(execution, test_case, runner)

        await use_case.execute(None)

        assert runner.executed_variables == [
            {
                "baseUrl": "https://env.test",
                "tenant": "acme",
                "retries": "3",
                "verbose": "true",
            }
        ]

    async def test_when_environment_has_secret_expect_runner_gets_value_and_results_never_do(
        self,
    ):
        test_case = _test_case()
        execution = _execution(
            test_case.identifier,
            environment_snapshot={"apiKey": SecretReference("env", "API_KEY")},
        )
        leaking_outcome = RunnerTestCaseOutcome(
            status=ResultStatus.FAILED,
            started_at=_STARTED_AT,
            finished_at=_FINISHED_AT,
            actions=(
                RunnerActionOutcome(
                    "request",
                    "HTTP",
                    ResultStatus.FAILED,
                    _STARTED_AT,
                    _FINISHED_AT,
                    actual={"request": {"headers": {"X-Custom-Token": "s3cr3t-value"}}},
                    error_code="TAVERN_ASSERTION_FAILED",
                    error_message="Status 401 for token s3cr3t-value",
                ),
            ),
            error_code="TAVERN_ASSERTION_FAILED",
            error_message="Status 401 for token s3cr3t-value",
        )
        runner = _Runner(outcome=leaking_outcome)
        results = _Results()
        use_case = _use_case(
            execution, test_case, runner, results, secrets={"API_KEY": "s3cr3t-value"}
        )

        await use_case.execute(None)

        result, actions, _ = results.saved[0]
        assert runner.executed_variables[0]["apiKey"] == "s3cr3t-value"
        assert result.error_message == "Status 401 for token [REDACTED]"
        assert actions[0].actual == {"request": {"headers": {"X-Custom-Token": "[REDACTED]"}}}
        assert actions[0].error_message == "Status 401 for token [REDACTED]"
        assert "s3cr3t-value" not in repr(results.saved)

    async def test_when_secret_cannot_be_resolved_expect_error_execution_without_running(
        self, caplog
    ):
        test_case = _test_case()
        execution = _execution(
            test_case.identifier,
            environment_snapshot={"apiKey": SecretReference("env", "MISSING")},
        )
        runner = _Runner()
        results = _Results()
        use_case = _use_case(execution, test_case, runner, results)

        processed = await use_case.execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.ERROR
        assert runner.executed_test_case_ids == []
        assert results.saved == []
        assert isinstance(caplog.records[-1].exc_info[1], SecretResolutionException)

    async def test_when_test_case_exceeds_its_timeout_expect_error_result_and_next_case_runs(
        self,
    ):
        slow_case = _test_case(timeout_seconds=1)
        next_case = _test_case()
        execution = replace(
            _execution(slow_case.identifier),
            test_case_ids=(slow_case.identifier, next_case.identifier),
        )
        runner = _HangingRunner()
        results = _Results()
        use_case = _use_case(execution, slow_case, runner, results, other_test_cases=(next_case,))

        processed = await use_case.execute(None)

        timed_out, _, _ = results.saved[0]
        passed, _, _ = results.saved[1]
        assert timed_out.test_case_id == slow_case.identifier
        assert timed_out.status is ResultStatus.ERROR
        assert timed_out.error_code == "TEST_TIMEOUT"
        assert timed_out.error_message == "Test Case exceeded its timeout of 1 seconds"
        assert passed.status is ResultStatus.PASSED
        assert processed is not None
        assert processed.status is ExecutionStatus.PARTIALLY_FAILED

    async def test_when_plan_timeout_elapses_expect_remaining_test_cases_not_run(self):
        first_case = _test_case()
        second_case = _test_case()
        execution = replace(
            _execution(first_case.identifier),
            test_case_ids=(first_case.identifier, second_case.identifier),
        )
        runner = _HangingRunner()
        results = _Results()
        use_case = _use_case(
            execution,
            first_case,
            runner,
            results,
            test_plans=_TestPlans(_test_plan(timeout_seconds=1)),
            other_test_cases=(second_case,),
        )

        processed = await use_case.execute(None)

        assert [result.test_case_id for result, _, _ in results.saved] == [
            first_case.identifier,
            second_case.identifier,
        ]
        assert {result.status for result, _, _ in results.saved} == {ResultStatus.ERROR}
        assert {result.error_code for result, _, _ in results.saved} == {"TEST_TIMEOUT"}
        assert results.saved[0][0].error_message == "Test Plan exceeded its timeout of 1 seconds"
        assert runner.calls == 1
        assert processed is not None
        assert processed.status is ExecutionStatus.FAILED

    async def test_when_test_plan_is_missing_expect_error_execution_without_running(self, caplog):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        runner = _Runner()
        use_case = _use_case(execution, test_case, runner, test_plans=_TestPlans(None))

        processed = await use_case.execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.ERROR
        assert runner.executed_test_case_ids == []
        assert isinstance(caplog.records[-1].exc_info[1], EntityNotFoundException)
