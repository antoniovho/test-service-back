"""Use case that processes the next queued execution."""

# ruff: noqa: E501

import asyncio
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.application.services.execution.definition_compiler import (
    DefinitionCompiler,
)
from test_service.domain.application.services.execution.execution_result_mapper import (
    ExecutionResultMapper,
)
from test_service.domain.application.services.execution.execution_variables_resolver import (
    ExecutionVariables,
    ExecutionVariablesResolver,
)
from test_service.domain.application.services.execution.secret_redactor import (
    redact_test_case_outcome,
)
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.execution_manifest_integrity_exception import (
    ExecutionManifestIntegrityException,
)
from test_service.domain.model.exceptions.execution_runner_unavailable_exception import (
    ExecutionRunnerUnavailableException,
)
from test_service.domain.model.execution.execution import (
    Execution,
    ExecutionStatus,
    ResultStatus,
    TestResult,
)
from test_service.domain.ports.input.use_cases.execution.executions.process_next_execution_use_case import (
    ProcessNextExecutionUseCase,
)
from test_service.domain.ports.output.executions.execution_cancellation_port import (
    ExecutionCancellationPort,
)
from test_service.domain.ports.output.persistence.executions.execution_persistence_port import (
    ExecutionPersistencePort,
)
from test_service.domain.ports.output.persistence.executions.execution_results_persistence_port import (
    ExecutionResultsPersistencePort,
)
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (
    PreconditionPersistencePort,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (
    TestPlanPersistencePort,
)
from test_service.domain.ports.output.runners.runner_dtos import (
    CompiledTestCase,
    RunnerActionOutcome,
    RunnerTestCaseOutcome,
)
from test_service.domain.ports.output.runners.runner_port import RunnerPort

logger = logging.getLogger(__name__)

TEST_TIMEOUT_ERROR_CODE = "TEST_TIMEOUT"
CANCELLATION_POLL_INTERVAL_SECONDS = 0.5


@dataclass(frozen=True, slots=True, order=True)
class _Deadline:
    """Event-loop clock instant after which a run must stop, and the limit that set it."""

    at: float
    message: str = field(compare=False)


@dataclass(frozen=True, slots=True)
class _PreconditionOutcome:
    """Context and terminal result produced while executing Test Case preconditions."""

    variables: Mapping[str, str]
    secrets: frozenset[str]
    evidence: tuple[RunnerActionOutcome, ...]
    terminal_result: tuple[ResultStatus, str, str] | None = None


def _clock() -> float:
    return asyncio.get_running_loop().time()


class ProcessNextExecutionUseCaseImpl(ProcessNextExecutionUseCase):
    """Claim and process the next queued execution."""

    def __init__(
        self,
        executions: ExecutionPersistencePort,
        results: ExecutionResultsPersistencePort,
        test_cases: TestCasePersistencePort,
        preconditions: PreconditionPersistencePort,
        test_plans: TestPlanPersistencePort,
        compiler: DefinitionCompiler,
        runner: RunnerPort,
        cancellations: ExecutionCancellationPort,
        variables_resolver: ExecutionVariablesResolver,
    ) -> None:
        self._executions = executions
        self._results = results
        self._test_cases = test_cases
        self._preconditions = preconditions
        self._test_plans = test_plans
        self._compiler = compiler
        self._result_mapper = ExecutionResultMapper()
        self._runner = runner
        self._cancellations = cancellations
        self._variables_resolver = variables_resolver

    async def execute(self, _: None) -> Execution | None:
        await self._executions.recover_stale_running()
        execution = await self._executions.claim_next_created()

        if execution is None:
            return None
        cancellation = self._cancellations.register(execution.identifier)
        cancellation_monitor = asyncio.create_task(
            self._watch_persisted_cancellation(execution.identifier, cancellation)
        )

        try:
            # Ensure the execution is compatible with the current runner before proceeding.
            if (
                execution.runner_identifier != self._runner.identifier
                or execution.runner_version != self._runner.version
            ):
                raise ExecutionRunnerUnavailableException(
                    execution.identifier,
                    execution.runner_identifier,
                    execution.runner_version,
                    self._runner.identifier,
                    self._runner.version,
                )
            # Resolve execution variables and execute the test plan.
            variables = await self._variables_resolver.resolve(execution.environment_snapshot)
            outcomes = await self._execute(
                execution,
                cancellation,
                variables,
            )
            # If the execution was cancelled during the test plan execution, handle it accordingly.
            if cancellation.is_set():
                return await self._executions.transition_execution(
                    execution.cancel(datetime.now(UTC)),
                    (ExecutionStatus.RUNNING,),
                )
            # Transition the execution to the appropriate final state based on the outcomes.
            return await self._executions.transition_execution(
                execution.complete(
                    self._execution_status(outcomes),
                    datetime.now(UTC),
                ),
                (ExecutionStatus.RUNNING,),
            )
        except Exception:
            logger.exception(
                "Execution '%s' failed with runner '%s' version '%s'.",
                execution.identifier,
                self._runner.identifier,
                self._runner.version,
            )
            return await self._executions.transition_execution(
                execution.complete(
                    ExecutionStatus.ERROR,
                    datetime.now(UTC),
                ),
                (ExecutionStatus.RUNNING,),
            )

        finally:
            cancellation_monitor.cancel()
            await asyncio.gather(cancellation_monitor, return_exceptions=True)
            self._cancellations.unregister(execution.identifier)

    async def _watch_persisted_cancellation(
        self, execution_id, cancellation: asyncio.Event
    ) -> None:
        """Observe cancellation written by another application replica."""
        polling_failed = False
        while not cancellation.is_set():
            try:
                execution = await self._executions.find_execution(execution_id)
            except Exception:
                if not polling_failed:
                    logger.exception(
                        "Failed to poll persisted cancellation for execution '%s'.", execution_id
                    )
                    polling_failed = True
            else:
                polling_failed = False
                if execution is None or execution.status is ExecutionStatus.CANCELLED:
                    cancellation.set()
                    return
            await asyncio.sleep(CANCELLATION_POLL_INTERVAL_SECONDS)

    async def _execute(
        self,
        execution: Execution,
        cancellation: asyncio.Event,
        variables: ExecutionVariables,
    ) -> tuple[ResultStatus, ...]:
        """Execute every Test Case captured by the accepted execution manifest."""

        # Ensure the execution has test cases to run.
        if not execution.test_case_ids:
            raise ExecutionManifestIntegrityException(execution.identifier)

        # Retrieve the associated test plan to enforce its timeout and validate its existence.
        test_plan = await self._test_plans.find_by_id(execution.test_plan_id)
        if test_plan is None:
            raise EntityNotFoundException("Test plan", str(execution.test_plan_id))
        plan_deadline = _Deadline(
            _clock() + test_plan.timeout_seconds,
            f"Test Plan exceeded its timeout of {test_plan.timeout_seconds} seconds",
        )

        statuses: list[ResultStatus] = []

        for identifier in execution.test_case_ids:
            if cancellation.is_set():
                break

            # Retrieve the test case to enforce its timeout and validate its existence.
            test_case = await self._test_cases.find_by_id(identifier)
            if test_case is None:
                raise ExecutionManifestIntegrityException(execution.identifier, identifier)
            deadline = min(
                plan_deadline,
                _Deadline(
                    _clock() + test_case.timeout_seconds,
                    f"Test Case exceeded its timeout of {test_case.timeout_seconds} seconds",
                ),
            )
            # Execute the test case within the enforced deadline.
            status = await self._execute_test_case(
                execution,
                test_case,
                cancellation,
                variables,
                deadline,
            )

            statuses.append(status)

        return tuple(statuses)

    async def _execute_test_case(
        self,
        execution: Execution,
        test_case,
        cancellation: asyncio.Event,
        variables: ExecutionVariables,
        deadline: _Deadline,
    ) -> ResultStatus:
        """Run a Test Case and persist its outcome, a blocking precondition failure or a timeout."""
        started_at = datetime.now(UTC)

        # Execute preconditions for the test case.
        preconditions = await self._execute_preconditions(
            execution, test_case, cancellation, variables, deadline
        )
        if preconditions.terminal_result is not None:
            terminal_status, error_code, error_message = preconditions.terminal_result
            return await self._save_terminal_result(
                execution,
                test_case.identifier,
                started_at,
                terminal_status,
                error_code,
                error_message,
                preconditions.evidence,
            )

        # Prepare the variables and evidence for the test case execution.
        variable_values = dict(preconditions.variables)
        variable_secrets = set(preconditions.secrets)
        precondition_evidence = preconditions.evidence

        # Compile the test case definition.
        compiled = self._compiler.compile(
            test_case.identifier,
            test_case.definition,
            variable_values,
        )

        if not self._runner.supports(frozenset(item.action_type for item in compiled.actions)):
            error_code = "RUNNER_UNSUPPORTED_TEST_CASE"
            error_message = (
                f"Execution '{execution.identifier}' cannot run Test Case "
                f"'{test_case.identifier}' because runner '{self._runner.identifier}' "
                "does not support its definition."
            )
            return await self._save_blocked(
                execution,
                test_case.identifier,
                started_at,
                error_code,
                error_message,
                tuple(precondition_evidence),
            )

        # Run the compiled test case and capture its outcome.
        test_case_outcome = await self._run(compiled, cancellation, deadline)

        if test_case_outcome is None:
            return await self._save_timed_out(
                execution,
                test_case.identifier,
                started_at,
                deadline,
                tuple(precondition_evidence),
            )

        # Redact sensitive information from the test case outcome before storing the results.
        outcome = redact_test_case_outcome(
            test_case_outcome,
            variable_secrets,
        )

        result_id = uuid4()
        actions = self._result_mapper.to_action_results(
            result_id, (*precondition_evidence, *outcome.actions)
        )

        await self._results.save_results(
            TestResult(
                identifier=result_id,
                execution_id=execution.identifier,
                test_case_id=test_case.identifier,
                status=outcome.status,
                created_at=outcome.started_at,
                started_at=outcome.started_at,
                finished_at=outcome.finished_at,
                duration_ms=int((outcome.finished_at - outcome.started_at).total_seconds() * 1000),
                error_code=outcome.error_code,
                error_message=outcome.error_message,
            ),
            actions,  # artifacts ?
        )

        return outcome.status

    async def _execute_preconditions(
        self,
        execution: Execution,
        test_case,
        cancellation: asyncio.Event,
        variables: ExecutionVariables,
        deadline: _Deadline,
    ) -> _PreconditionOutcome:
        """Run prerequisites and return the context/evidence needed by the Test Case."""
        variable_values = dict(variables.values)
        variable_secrets = set(variables.secrets)
        evidence: list[RunnerActionOutcome] = []

        for reference in test_case.preconditions:
            precondition = await self._preconditions.find_by_id(reference.identifier)
            if precondition is None:
                return _PreconditionOutcome(
                    variable_values,
                    frozenset(variable_secrets),
                    tuple(evidence),
                    (
                        ResultStatus.BLOCKED,
                        "PRECONDITION_MISSING",
                        f"Execution '{execution.identifier}' cannot run Test Case "
                        f"'{test_case.identifier}' because precondition "
                        f"'{reference.identifier}' is unavailable.",
                    ),
                )

            compiled = self._compiler.compile(
                precondition.identifier,
                precondition.validation_definition,
                variable_values,
            )
            if not self._runner.supports(frozenset(item.action_type for item in compiled.actions)):
                return _PreconditionOutcome(
                    variable_values,
                    frozenset(variable_secrets),
                    tuple(evidence),
                    (
                        ResultStatus.BLOCKED,
                        "RUNNER_UNSUPPORTED_PRECONDITION",
                        f"Execution '{execution.identifier}' cannot run Test Case "
                        f"'{test_case.identifier}' because runner '{self._runner.identifier}' "
                        f"does not support precondition '{reference.identifier}'.",
                    ),
                )
            # Run the compiled precondition and handle its outcome.
            outcome = await self._run(compiled, cancellation, deadline)
            if outcome is None:
                return _PreconditionOutcome(
                    variable_values,
                    frozenset(variable_secrets),
                    tuple(evidence),
                    (ResultStatus.ERROR, TEST_TIMEOUT_ERROR_CODE, deadline.message),
                )
            # Update variable values and secrets with the outcome of the precondition for subsequent steps.
            variable_values.update(outcome.variables)
            variable_secrets.update(value for value in outcome.variables.values() if value)
            outcome = redact_test_case_outcome(outcome, variable_secrets)
            evidence.extend(self._result_mapper.precondition_evidence(precondition, outcome))

            if outcome.status is not ResultStatus.PASSED:
                return _PreconditionOutcome(
                    variable_values,
                    frozenset(variable_secrets),
                    tuple(evidence),
                    (
                        ResultStatus.BLOCKED,
                        "PRECONDITION_FAILED",
                        f"Execution '{execution.identifier}' cannot run Test Case "
                        f"'{test_case.identifier}' because precondition "
                        f"'{reference.identifier}' did not pass.",
                    ),
                )

        return _PreconditionOutcome(
            variable_values,
            frozenset(variable_secrets),
            tuple(evidence),
        )

    async def _run(
        self, compiled: CompiledTestCase, cancellation: asyncio.Event, deadline: _Deadline
    ) -> RunnerTestCaseOutcome | None:
        """Run the runner until the deadline; return None when the deadline stopped it."""
        if _clock() >= deadline.at:
            return None
        limit = asyncio.timeout_at(deadline.at)
        try:
            async with limit:
                return await self._runner.execute(compiled, cancellation)
        except TimeoutError:
            if limit.expired():
                return None
            raise

    async def _save_blocked(
        self,
        execution: Execution,
        test_case_id,
        started_at: datetime,
        error_code: str,
        error_message: str,
        evidence: tuple[RunnerActionOutcome, ...] = (),
    ) -> ResultStatus:
        """Persist a blocked Test Case result with its normalized failure context."""
        return await self._save_terminal_result(
            execution,
            test_case_id,
            started_at,
            ResultStatus.BLOCKED,
            error_code,
            error_message,
            evidence,
        )

    async def _save_timed_out(
        self,
        execution: Execution,
        test_case_id,
        started_at: datetime,
        deadline: _Deadline,
        evidence: tuple[RunnerActionOutcome, ...] = (),
    ) -> ResultStatus:
        """Persist an ERROR Test Case result for a run stopped by its deadline."""
        return await self._save_terminal_result(
            execution,
            test_case_id,
            started_at,
            ResultStatus.ERROR,
            TEST_TIMEOUT_ERROR_CODE,
            deadline.message,
            evidence,
        )

    async def _save_terminal_result(
        self,
        execution: Execution,
        test_case_id,
        started_at: datetime,
        status: ResultStatus,
        error_code: str,
        error_message: str,
        evidence: tuple[RunnerActionOutcome, ...] = (),
    ) -> ResultStatus:
        """Persist a terminal Test Case result without a full runner outcome.

        Optional evidence, such as completed precondition actions, is persisted
        with the result.
        """
        finished_at = datetime.now(UTC)
        result_id = uuid4()

        await self._results.save_results(
            TestResult(
                result_id,
                execution.identifier,
                test_case_id,
                status,
                started_at,
                started_at,
                finished_at,
                int((finished_at - started_at).total_seconds() * 1000),
                error_code,
                error_message,
            ),
            self._result_mapper.to_action_results(result_id, evidence),
        )

        return status

    @staticmethod
    def _execution_status(
        statuses: tuple[ResultStatus, ...],
    ) -> ExecutionStatus:
        """Aggregate Test Case outcomes into the final execution status."""
        if not statuses:
            return ExecutionStatus.PASSED

        failed = sum(status is not ResultStatus.PASSED for status in statuses)

        if failed == 0:
            return ExecutionStatus.PASSED

        if failed == len(statuses):
            return ExecutionStatus.FAILED

        return ExecutionStatus.PARTIALLY_FAILED
