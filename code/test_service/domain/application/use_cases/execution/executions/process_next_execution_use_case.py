"""Use case that processes the next queued execution."""

# ruff: noqa: E501

import asyncio
import logging
from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.application.services.execution.definition_compiler import (
    DefinitionCompiler,
)
from test_service.domain.application.services.execution.execution_variables_resolver import (
    ExecutionVariables,
    ExecutionVariablesResolver,
)
from test_service.domain.application.services.execution.secret_redactor import (
    redact_test_case_outcome,
)
from test_service.domain.model.exceptions.execution_manifest_integrity_exception import (
    ExecutionManifestIntegrityException,
)
from test_service.domain.model.exceptions.execution_runner_unavailable_exception import (
    ExecutionRunnerUnavailableException,
)
from test_service.domain.model.execution.execution import (
    ActionResult,
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
from test_service.domain.ports.output.runners.runner_port import RunnerPort

logger = logging.getLogger(__name__)


class ProcessNextExecutionUseCaseImpl(ProcessNextExecutionUseCase):
    """Claim and process the next queued execution."""

    def __init__(
        self,
        executions: ExecutionPersistencePort,
        results: ExecutionResultsPersistencePort,
        test_cases: TestCasePersistencePort,
        preconditions: PreconditionPersistencePort,
        compiler: DefinitionCompiler,
        runner: RunnerPort,
        cancellations: ExecutionCancellationPort,
        variables_resolver: ExecutionVariablesResolver,
    ) -> None:
        self._executions = executions
        self._results = results
        self._test_cases = test_cases
        self._preconditions = preconditions
        self._compiler = compiler
        self._runner = runner
        self._cancellations = cancellations
        self._variables_resolver = variables_resolver

    async def execute(self, _: None) -> Execution | None:
        execution = await self._executions.claim_next_created()

        if execution is None:
            return None
        cancellation = self._cancellations.register(execution.identifier)

        try:
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
            variables = await self._variables_resolver.resolve(execution.environment_snapshot)
            outcomes = await self._execute(
                execution,
                cancellation,
                variables,
            )
            if cancellation.is_set():
                return await self._executions.save_execution(execution.cancel(datetime.now(UTC)))

            return await self._executions.save_execution(
                execution.complete(
                    self._execution_status(outcomes),
                    datetime.now(UTC),
                )
            )
        except Exception:
            logger.exception(
                "Execution '%s' failed with runner '%s' version '%s'.",
                execution.identifier,
                self._runner.identifier,
                self._runner.version,
            )
            return await self._executions.save_execution(
                execution.complete(
                    ExecutionStatus.ERROR,
                    datetime.now(UTC),
                )
            )

        finally:
            self._cancellations.unregister(execution.identifier)

    async def _execute(
        self,
        execution: Execution,
        cancellation: asyncio.Event,
        variables: ExecutionVariables,
    ) -> tuple[ResultStatus, ...]:
        """Execute every Test Case captured by the accepted execution manifest."""
        if not execution.test_case_ids:
            raise ExecutionManifestIntegrityException(execution.identifier)

        statuses: list[ResultStatus] = []

        for identifier in execution.test_case_ids:
            if cancellation.is_set():
                break

            test_case = await self._test_cases.find_by_id(identifier)

            if test_case is None:
                raise ExecutionManifestIntegrityException(execution.identifier, identifier)

            status = await self._execute_test_case(
                execution,
                test_case,
                cancellation,
                variables,
            )

            statuses.append(status)

        return tuple(statuses)

    async def _execute_test_case(
        self,
        execution: Execution,
        test_case,
        cancellation: asyncio.Event,
        variables: ExecutionVariables,
    ) -> ResultStatus:
        """Run a Test Case and persist its outcome or a blocking precondition failure."""
        started_at = datetime.now(UTC)

        for reference in test_case.preconditions:
            precondition = await self._preconditions.find_by_id(reference.identifier)

            if precondition is None:
                error_code = "PRECONDITION_MISSING"
                error_message = (
                    f"Execution '{execution.identifier}' cannot run Test Case "
                    f"'{test_case.identifier}' because precondition "
                    f"'{reference.identifier}' is unavailable."
                )
                return await self._save_blocked(
                    execution,
                    test_case.identifier,
                    started_at,
                    error_code,
                    error_message,
                )

            compiled = self._compiler.compile(
                precondition.identifier,
                precondition.validation_definition,
                variables.values,
            )

            if not self._runner.supports(frozenset(item.action_type for item in compiled.actions)):
                return await self._save_blocked(
                    execution,
                    test_case.identifier,
                    started_at,
                    "RUNNER_UNSUPPORTED_PRECONDITION",
                    f"Execution '{execution.identifier}' cannot run Test Case "
                    f"'{test_case.identifier}' because runner '{self._runner.identifier}' "
                    f"does not support precondition '{reference.identifier}'.",
                )

            outcome = await self._runner.execute(
                compiled,
                cancellation,
            )

            if outcome.status is not ResultStatus.PASSED:
                return await self._save_blocked(
                    execution,
                    test_case.identifier,
                    started_at,
                    "PRECONDITION_FAILED",
                    f"Execution '{execution.identifier}' cannot run Test Case "
                    f"'{test_case.identifier}' because precondition "
                    f"'{reference.identifier}' did not pass.",
                )

        compiled = self._compiler.compile(
            test_case.identifier,
            test_case.definition,
            variables.values,
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
            )

        test_case_outcome = await self._runner.execute(compiled, cancellation)
        # Redact sensitive information from the test case outcome before persisting it.
        outcome = redact_test_case_outcome(
            test_case_outcome,
            variables.secrets,
        )

        result_id = uuid4()

        actions = tuple(
            ActionResult(
                identifier=uuid4(),
                test_result_id=result_id,
                action_id=item.action_id,
                action_type=item.action_type,
                status=item.status,
                created_at=item.started_at,
                expected=item.expected,
                actual=item.actual,
                output=item.output,
                started_at=item.started_at,
                finished_at=item.finished_at,
                duration_ms=int((item.finished_at - item.started_at).total_seconds() * 1000),
                error_code=item.error_code,
                error_message=item.error_message,
            )
            for item in outcome.actions
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

    async def _save_blocked(
        self,
        execution: Execution,
        test_case_id,
        started_at: datetime,
        error_code: str,
        error_message: str,
    ) -> ResultStatus:
        """Persist a blocked Test Case result with its normalized failure context."""
        finished_at = datetime.now(UTC)

        await self._results.save_results(
            TestResult(
                uuid4(),
                execution.identifier,
                test_case_id,
                ResultStatus.BLOCKED,
                started_at,
                started_at,
                finished_at,
                int((finished_at - started_at).total_seconds() * 1000),
                error_code,
                error_message,
            ),
            (),
        )

        return ResultStatus.BLOCKED

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
