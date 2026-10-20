import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest

from test_service.domain.application.services.execution.definition_compiler import (
    DefinitionCompiler,
)
from test_service.domain.application.services.execution.execution_variables_resolver import (
    ExecutionVariables,
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
from test_service.domain.model.exceptions.execution_manifest_integrity_exception import (
    ExecutionManifestIntegrityException,
)
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
from test_service.domain.ports.output.executions.execution_cancellation_port import (
    ExecutionCancellationPort,
)
from test_service.domain.ports.output.persistence.executions.execution_persistence_port import (
    ExecutionPersistencePort,
)
from test_service.domain.ports.output.persistence.executions.execution_results_persistence_port import (  # noqa: E501
    ExecutionResultsPersistencePort,
)
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (
    TestPlanPersistencePort,
)
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
    def __init__(self, execution: Execution | None) -> None:
        self._execution = execution
        self.current = execution
        self.saved: list[Execution] = []
        self.transitions: list[tuple[Execution, tuple[ExecutionStatus, ...]]] = []
        self.find_requested_ids = []
        self.recovery_calls = 0
        self.calls: list[str] = []

    async def claim_next_created(self) -> Execution | None:
        self.calls.append("claim")
        return self._execution

    async def mark_stale_running_as_error(self) -> int:
        self.recovery_calls += 1
        self.calls.append("recover")
        return 0

    async def find_execution(self, identifier):
        self.find_requested_ids.append(identifier)
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
        self.requested_ids = []

    async def find_by_id(self, identifier):
        self.requested_ids.append(identifier)
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
        supported: bool = True,
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
        self._supported = supported

    def supports(self, action_types: frozenset[str]) -> bool:
        return self._supported

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


class _ActionAwareRunner(_SequenceRunner):
    def __init__(
        self, supported_action_types: frozenset[str], *outcomes: RunnerTestCaseOutcome
    ) -> None:
        super().__init__(*outcomes)
        self.supported_action_types = supported_action_types
        self.requested_action_types: list[frozenset[str]] = []

    def supports(self, action_types: frozenset[str]) -> bool:
        self.requested_action_types.append(action_types)
        return action_types == self.supported_action_types


class _ConcurrentCancellationRunner(_Runner):
    def __init__(self, executions: _Executions) -> None:
        super().__init__()
        self._executions = executions

    async def execute(self, test_case, cancellation: asyncio.Event) -> RunnerTestCaseOutcome:
        self._executions.current = self._executions.current.cancel(_FINISHED_AT)
        await asyncio.sleep(0)
        return await super().execute(test_case, cancellation)


class _LocalCancellationRunner(_Runner):
    async def execute(self, test_case, cancellation: asyncio.Event) -> RunnerTestCaseOutcome:
        cancellation.set()
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


def _process_next_execution_use_case(
    executions: _Executions,
    results: _Results,
    test_cases: _TestCases,
    preconditions: _Preconditions,
    test_plans: _TestPlans,
    runner: _Runner,
    cancellations: _Cancellations,
    variables_resolver: ExecutionVariablesResolver,
) -> ProcessNextExecutionUseCaseImpl:
    return ProcessNextExecutionUseCaseImpl(
        cast(ExecutionPersistencePort, executions),
        cast(ExecutionResultsPersistencePort, results),
        cast(TestCasePersistencePort, test_cases),
        cast(PreconditionPersistencePort, preconditions),
        cast(TestPlanPersistencePort, test_plans),
        DefinitionCompiler(),
        runner,
        cast(ExecutionCancellationPort, cancellations),
        variables_resolver,
    )


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
    return _process_next_execution_use_case(
        _Executions(execution),
        results or _Results(),
        _TestCases(test_case, *other_test_cases),
        _Preconditions(*preconditions),
        test_plans or _TestPlans(_test_plan()),
        runner,
        _Cancellations(),
        ExecutionVariablesResolver(_SecretResolver(secrets)),
    )


class TestProcessNextExecutionUseCase:
    async def test_when_no_execution_is_queued_expect_none_after_stale_recovery(self):
        test_case = _test_case()
        executions = _Executions(None)
        cancellations = _Cancellations()
        use_case = _process_next_execution_use_case(
            executions,
            _Results(),
            _TestCases(test_case),
            _Preconditions(),
            _TestPlans(_test_plan()),
            _Runner(),
            cancellations,
            ExecutionVariablesResolver(_SecretResolver()),
        )

        processed = await use_case.execute(None)

        assert processed is None
        assert executions.calls == ["recover", "claim"]
        assert cancellations.registered == []
        assert cancellations.unregistered == []

    async def test_when_processing_next_execution_expect_stale_executions_recovered_first(self):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        executions = _Executions(execution)
        use_case = _process_next_execution_use_case(
            executions,
            _Results(),
            _TestCases(test_case),
            _Preconditions(),
            _TestPlans(_test_plan()),
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
        use_case = _process_next_execution_use_case(
            executions,
            results,
            _TestCases(test_case),
            _Preconditions(),
            _TestPlans(_test_plan()),
            runner,
            cancellations,
            ExecutionVariablesResolver(_SecretResolver()),
        )

        processed = await use_case.execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.PASSED
        assert runner.executed_test_case_ids == [str(test_case.identifier)]
        assert results.saved[0][0].test_case_id == test_case.identifier
        assert cancellations.registered == [execution.identifier]
        assert cancellations.unregistered == [execution.identifier]

    async def test_when_runner_does_not_support_test_case_expect_blocked_result_without_execution(
        self,
    ):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        results = _Results()
        runner = _Runner(supported=False)

        processed = await _use_case(execution, test_case, runner, results).execute(None)

        result, actions, artifacts = results.saved[0]
        assert processed is not None
        assert processed.status is ExecutionStatus.FAILED
        assert runner.executed_test_case_ids == []
        assert result.execution_id == execution.identifier
        assert result.test_case_id == test_case.identifier
        assert result.status is ResultStatus.BLOCKED
        assert result.error_code == "RUNNER_UNSUPPORTED_TEST_CASE"
        assert result.error_message == (
            f"Execution '{execution.identifier}' cannot run Test Case "
            f"'{test_case.identifier}' because runner 'runner' does not support its definition."
        )
        assert actions == ()
        assert artifacts == ()

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

    async def test_when_precondition_missing_expect_accumulated_context_preserved(
        self,
    ):
        completed_precondition_id = uuid4()
        missing_precondition_id = uuid4()
        test_case = _test_case(
            preconditions=(
                PreconditionReference(completed_precondition_id, "authenticated", 1),
                PreconditionReference(missing_precondition_id, "profile", 1),
            )
        )
        precondition = Precondition(
            identifier=completed_precondition_id,
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
                ),
            ),
            variables={"sessionToken": "temporary-token"},
        )
        execution = _execution(test_case.identifier)
        runner = _SequenceRunner(precondition_outcome)
        use_case = _use_case(
            execution,
            test_case,
            runner,
            preconditions=(precondition,),
        )

        outcome = await use_case._execute_preconditions(
            execution,
            test_case,
            asyncio.Event(),
            ExecutionVariables({"environment": "value"}, frozenset({"environment-secret"})),
            process_next_execution_use_case._Deadline(float("inf"), "not reached"),
        )

        assert outcome.variables == {"environment": "value", "sessionToken": "temporary-token"}
        assert outcome.secrets == frozenset({"environment-secret", "temporary-token"})
        assert len(outcome.evidence) == 2
        assert runner.executed_variables == [{"environment": "value"}]
        assert outcome.terminal_result == (
            ResultStatus.BLOCKED,
            "PRECONDITION_MISSING",
            f"Execution '{execution.identifier}' cannot run Test Case "
            f"'{test_case.identifier}' because precondition "
            f"'{missing_precondition_id}' is unavailable.",
        )

    async def test_when_runner_does_not_support_precondition_expect_blocked_result(
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
        execution = _execution(test_case.identifier)
        results = _Results()
        runner = _Runner(supported=False)

        processed = await _use_case(
            execution,
            test_case,
            runner,
            results,
            preconditions=(precondition,),
        ).execute(None)

        result, actions, artifacts = results.saved[0]
        assert processed is not None
        assert processed.status is ExecutionStatus.FAILED
        assert runner.executed_test_case_ids == []
        assert result.execution_id == execution.identifier
        assert result.test_case_id == test_case.identifier
        assert result.status is ResultStatus.BLOCKED
        assert result.error_code == "RUNNER_UNSUPPORTED_PRECONDITION"
        assert result.error_message == (
            f"Execution '{execution.identifier}' cannot run Test Case "
            f"'{test_case.identifier}' because runner 'runner' does not support precondition "
            f"'{precondition_id}'."
        )
        assert actions == ()
        assert artifacts == ()

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

    async def test_when_executing_test_case_expect_cancellation_is_forwarded_to_preconditions(
        self, monkeypatch
    ):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        results = _Results()
        use_case = _use_case(execution, test_case, _Runner(), results)
        cancellation = asyncio.Event()
        received_cancellations: list[asyncio.Event] = []

        async def execute_preconditions(*arguments):
            received_cancellations.append(arguments[2])
            return process_next_execution_use_case._PreconditionOutcome(
                {},
                frozenset(),
                (),
                (ResultStatus.BLOCKED, "PRECONDITION_MISSING", "missing prerequisite"),
            )

        monkeypatch.setattr(use_case, "_execute_preconditions", execute_preconditions)

        status = await use_case._execute_test_case(
            execution,
            test_case,
            cancellation,
            ExecutionVariables({}, frozenset()),
            process_next_execution_use_case._Deadline(float("inf"), "not reached"),
        )

        assert status is ResultStatus.BLOCKED
        assert received_cancellations == [cancellation]
        assert results.saved[0][0].error_code == "PRECONDITION_MISSING"

    async def test_when_saving_terminal_result_expect_generated_result_identifier(self):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        results = _Results()
        use_case = _use_case(execution, test_case, _Runner(), results)

        status = await use_case._save_terminal_result(
            execution,
            test_case.identifier,
            _STARTED_AT,
            ResultStatus.BLOCKED,
            "PRECONDITION_MISSING",
            "missing prerequisite",
        )

        result, actions, artifacts = results.saved[0]
        assert status is ResultStatus.BLOCKED
        assert isinstance(result.identifier, UUID)
        assert result.execution_id == execution.identifier
        assert result.test_case_id == test_case.identifier
        assert result.status is ResultStatus.BLOCKED
        assert result.error_code == "PRECONDITION_MISSING"
        assert result.error_message == "missing prerequisite"
        assert actions == ()
        assert artifacts == ()

    async def test_when_terminal_evidence_has_diagnostic_trace_expect_database_artifact(self):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        results = _Results()
        use_case = _use_case(execution, test_case, _Runner(), results)
        evidence = (
            RunnerActionOutcome(
                "health",
                "HTTP",
                ResultStatus.ERROR,
                _STARTED_AT,
                _FINISHED_AT,
                diagnostic_trace="sanitized diagnostic traceback",
            ),
        )

        await use_case._save_terminal_result(
            execution,
            test_case.identifier,
            _STARTED_AT,
            ResultStatus.BLOCKED,
            "PRECONDITION_FAILED",
            "precondition did not pass",
            evidence,
        )

        result, actions, artifacts = results.saved[0]
        assert len(artifacts) == 1
        assert artifacts[0].test_result_id == result.identifier
        assert artifacts[0].action_result_id == actions[0].identifier
        assert artifacts[0].content == "sanitized diagnostic traceback"
        assert artifacts[0].mime_type == "text/plain; charset=utf-8"

    async def test_when_cancel_wins_during_runner_expect_worker_preserves_cancelled_state(self):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        executions = _Executions(execution)
        use_case = _process_next_execution_use_case(
            executions,
            _Results(),
            _TestCases(test_case),
            _Preconditions(),
            _TestPlans(_test_plan()),
            _ConcurrentCancellationRunner(executions),
            _Cancellations(),
            ExecutionVariablesResolver(_SecretResolver()),
        )

        processed = await use_case.execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.CANCELLED
        assert processed.finished_at is not None
        assert executions.current.status is ExecutionStatus.CANCELLED
        assert executions.transitions[0][1] == (ExecutionStatus.RUNNING,)

    async def test_when_runner_signals_local_cancellation_expect_timestamped_cancelled_execution(
        self,
    ):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        executions = _Executions(execution)
        use_case = _process_next_execution_use_case(
            executions,
            _Results(),
            _TestCases(test_case),
            _Preconditions(),
            _TestPlans(_test_plan()),
            _LocalCancellationRunner(),
            _Cancellations(),
            ExecutionVariablesResolver(_SecretResolver()),
        )

        processed = await use_case.execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.CANCELLED
        assert processed.finished_at is not None
        assert executions.transitions[0][0].finished_at is not None

    async def test_when_cancel_is_persisted_by_another_replica_expect_running_runner_stopped(
        self,
    ):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        executions = _Executions(execution)
        runner = _WaitingForCancellationRunner()
        use_case = _process_next_execution_use_case(
            executions,
            _Results(),
            _TestCases(test_case),
            _Preconditions(),
            _TestPlans(_test_plan()),
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
        assert executions.transitions[0][0].status is ExecutionStatus.CANCELLED
        assert executions.find_requested_ids == [execution.identifier, execution.identifier]

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
        use_case = _process_next_execution_use_case(
            executions,
            _Results(),
            _TestCases(test_case),
            _Preconditions(),
            _TestPlans(_test_plan()),
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

        record = caplog.records[-1]
        assert processed is not None
        assert processed.status is ExecutionStatus.ERROR
        assert str(execution.identifier) in caplog.text
        assert "tavern" in caplog.text
        assert "other-runner" in caplog.text
        assert record.msg == "Execution '%s' failed with runner '%s' version '%s'."
        assert record.args == (execution.identifier, runner.identifier, runner.version)
        assert isinstance(record.exc_info[1], ExecutionRunnerUnavailableException)

    async def test_when_accepted_runner_version_is_unavailable_expect_error_with_version_context(
        self, caplog
    ):
        test_case = _test_case()
        execution = _execution(test_case.identifier, "tavern", "2.4.1")
        runner = _Runner("tavern", "1.0")
        use_case = _use_case(execution, test_case, runner)

        processed = await use_case.execute(None)

        error = caplog.records[-1].exc_info[1]
        assert processed is not None
        assert processed.status is ExecutionStatus.ERROR
        assert isinstance(error, ExecutionRunnerUnavailableException)
        assert error.execution_id == execution.identifier
        assert error.accepted_identifier == "tavern"
        assert error.accepted_version == "2.4.1"
        assert error.available_identifier == "tavern"
        assert error.available_version == "1.0"

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

    async def test_when_execution_manifest_has_no_test_cases_expect_error_without_running(self):
        test_case = _test_case()
        execution = replace(_execution(test_case.identifier), test_case_ids=())
        runner = _Runner()
        results = _Results()

        processed = await _use_case(execution, test_case, runner, results).execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.ERROR
        assert runner.executed_test_case_ids == []
        assert results.saved == []

    async def test_when_manifest_has_no_test_cases_expect_integrity_error_names_execution(self):
        test_case = _test_case()
        execution = replace(_execution(test_case.identifier), test_case_ids=())
        use_case = _use_case(execution, test_case, _Runner())
        cancellation = asyncio.Event()
        variables = ExecutionVariables({}, frozenset())

        with pytest.raises(ExecutionManifestIntegrityException, match=str(execution.identifier)):
            await use_case._execute(
                execution,
                cancellation,
                variables,
            )

    async def test_when_execution_references_unknown_test_case_expect_error_without_running(self):
        test_case = _test_case()
        execution = _execution(uuid4())
        runner = _Runner()
        results = _Results()

        processed = await _use_case(execution, test_case, runner, results).execute(None)

        assert processed is not None
        assert processed.status is ExecutionStatus.ERROR
        assert runner.executed_test_case_ids == []
        assert results.saved == []

    async def test_when_test_plan_is_missing_expect_exact_lookup_and_exception_context(self):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        test_plans = _TestPlans(None)
        use_case = _use_case(execution, test_case, _Runner(), test_plans=test_plans)
        cancellation = asyncio.Event()
        variables = ExecutionVariables({}, frozenset())

        with pytest.raises(
            EntityNotFoundException,
            match=f"Test plan '{execution.test_plan_id}' was not found",
        ):
            await use_case._execute(execution, cancellation, variables)

        assert test_plans.requested_ids == [execution.test_plan_id]

    async def test_when_manifest_references_missing_case_expect_exact_integrity_context(self):
        missing_test_case_id = uuid4()
        test_case = _test_case()
        execution = _execution(missing_test_case_id)
        use_case = _use_case(execution, test_case, _Runner())
        cancellation = asyncio.Event()
        variables = ExecutionVariables({}, frozenset())

        with pytest.raises(
            ExecutionManifestIntegrityException,
            match=(
                f"execution '{execution.identifier}' references missing test case snapshot "
                f"'{missing_test_case_id}'"
            ),
        ):
            await use_case._execute(execution, cancellation, variables)

    async def test_when_test_case_completes_expect_complete_result_metadata_and_action_linkage(
        self,
    ):
        test_case = _test_case()
        execution = _execution(test_case.identifier)
        outcome = RunnerTestCaseOutcome(
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
                    error_code="HTTP_500",
                ),
            ),
            error_code="HTTP_500",
            error_message="Service unavailable",
        )
        results = _Results()
        use_case = _use_case(execution, test_case, _Runner(outcome=outcome), results)

        status = await use_case._execute_test_case(
            execution,
            test_case,
            asyncio.Event(),
            ExecutionVariables({}, frozenset()),
            process_next_execution_use_case._Deadline(float("inf"), "not reached"),
        )

        result, actions, _ = results.saved[0]
        assert status is ResultStatus.FAILED
        assert isinstance(result.identifier, UUID)
        assert result.execution_id == execution.identifier
        assert result.test_case_id == test_case.identifier
        assert result.created_at == _STARTED_AT
        assert result.started_at == _STARTED_AT
        assert result.finished_at == _FINISHED_AT
        assert result.duration_ms == 1000
        assert result.error_code == "HTTP_500"
        assert result.error_message == "Service unavailable"
        assert actions[0].test_result_id == result.identifier

    async def test_when_test_case_is_unsupported_after_precondition_expect_evidence_preserved(self):
        precondition_id = uuid4()
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
        test_case = replace(
            _test_case(preconditions=(PreconditionReference(precondition_id, "authenticated", 1),)),
            definition=Definition(
                variables={},
                actions=(Action("verify", "SSE", {"url": "https://example.test/events"}),),
            ),
        )
        execution = _execution(test_case.identifier)
        precondition_outcome = RunnerTestCaseOutcome(
            status=ResultStatus.PASSED,
            started_at=_STARTED_AT,
            finished_at=_FINISHED_AT,
            actions=(),
        )
        results = _Results()
        runner = _ActionAwareRunner(frozenset({"HTTP"}), precondition_outcome)
        use_case = _use_case(execution, test_case, runner, results, preconditions=(precondition,))

        status = await use_case._execute_test_case(
            execution,
            test_case,
            asyncio.Event(),
            ExecutionVariables({}, frozenset()),
            process_next_execution_use_case._Deadline(float("inf"), "not reached"),
        )

        result, actions, _ = results.saved[0]
        assert status is ResultStatus.BLOCKED
        assert result.error_code == "RUNNER_UNSUPPORTED_TEST_CASE"
        assert runner.requested_action_types == [frozenset({"HTTP"}), frozenset({"SSE"})]
        assert [action.action_id for action in actions] == [f"precondition:{precondition_id}"]

    async def test_when_precondition_is_unsupported_expect_original_context_is_preserved(self):
        precondition_id = uuid4()
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
        test_case = _test_case(
            preconditions=(PreconditionReference(precondition_id, "authenticated", 1),)
        )
        execution = _execution(test_case.identifier)
        runner = _ActionAwareRunner(frozenset({"GRPC"}))
        use_case = _use_case(execution, test_case, runner, preconditions=(precondition,))
        variables = ExecutionVariables({"tenant": "zara"}, frozenset({"tenant-secret"}))

        outcome = await use_case._execute_preconditions(
            execution,
            test_case,
            asyncio.Event(),
            variables,
            process_next_execution_use_case._Deadline(float("inf"), "not reached"),
        )

        assert outcome.variables == {"tenant": "zara"}
        assert outcome.secrets == frozenset({"tenant-secret"})
        assert outcome.evidence == ()
        assert outcome.terminal_result == (
            ResultStatus.BLOCKED,
            "RUNNER_UNSUPPORTED_PRECONDITION",
            f"Execution '{execution.identifier}' cannot run Test Case "
            f"'{test_case.identifier}' because runner 'runner' does not support precondition "
            f"'{precondition_id}'.",
        )
        assert runner.requested_action_types == [frozenset({"HTTP"})]

    async def test_when_precondition_times_out_expect_original_context_and_deadline_preserved(
        self, monkeypatch
    ):
        precondition_id = uuid4()
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
        test_case = _test_case(
            preconditions=(PreconditionReference(precondition_id, "authenticated", 1),)
        )
        execution = _execution(test_case.identifier)
        use_case = _use_case(execution, test_case, _Runner(), preconditions=(precondition,))
        cancellation = asyncio.Event()
        deadline = process_next_execution_use_case._Deadline(42, "precondition deadline reached")
        variables = ExecutionVariables({"tenant": "zara"}, frozenset({"tenant-secret"}))
        received_cancellations: list[asyncio.Event] = []

        async def timed_out_run(compiled, received_cancellation, received_deadline):
            received_cancellations.append(received_cancellation)
            assert received_deadline == deadline
            return None

        monkeypatch.setattr(use_case, "_run", timed_out_run)

        outcome = await use_case._execute_preconditions(
            execution, test_case, cancellation, variables, deadline
        )

        assert outcome.variables == {"tenant": "zara"}
        assert outcome.secrets == frozenset({"tenant-secret"})
        assert outcome.evidence == ()
        assert outcome.terminal_result == (
            ResultStatus.ERROR,
            "TEST_TIMEOUT",
            "precondition deadline reached",
        )
        assert received_cancellations == [cancellation]

    async def test_when_precondition_fails_expect_updated_context_and_evidence_preserved(self):
        precondition_id = uuid4()
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
        test_case = _test_case(
            preconditions=(PreconditionReference(precondition_id, "authenticated", 1),)
        )
        execution = _execution(test_case.identifier)
        outcome = RunnerTestCaseOutcome(
            status=ResultStatus.FAILED,
            started_at=_STARTED_AT,
            finished_at=_FINISHED_AT,
            actions=(),
            variables={"sessionToken": "temporary-token"},
        )
        runner = _ActionAwareRunner(frozenset({"HTTP"}), outcome)
        use_case = _use_case(execution, test_case, runner, preconditions=(precondition,))

        precondition_outcome = await use_case._execute_preconditions(
            execution,
            test_case,
            asyncio.Event(),
            ExecutionVariables({"tenant": "zara"}, frozenset({"tenant-secret"})),
            process_next_execution_use_case._Deadline(float("inf"), "not reached"),
        )

        assert precondition_outcome.variables == {
            "tenant": "zara",
            "sessionToken": "temporary-token",
        }
        assert precondition_outcome.secrets == frozenset({"tenant-secret", "temporary-token"})
        assert len(precondition_outcome.evidence) == 1
        assert precondition_outcome.terminal_result == (
            ResultStatus.BLOCKED,
            "PRECONDITION_FAILED",
            f"Execution '{execution.identifier}' cannot run Test Case "
            f"'{test_case.identifier}' because precondition '{precondition_id}' did not pass.",
        )
