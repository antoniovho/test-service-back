"""Use case that processes the next queued execution."""

# ruff: noqa: E501

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.application.services.execution.definition_compiler import (
    DefinitionCompiler,
)
from test_service.domain.model.execution.execution import (
    ActionResult,
    Execution,
    ExecutionStatus,
    ResultStatus,
    TestResult,
)
from test_service.domain.model.lifecycle import VersionStatus
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
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)
from test_service.domain.ports.output.runners.runner_port import RunnerPort


class ProcessNextExecutionUseCaseImpl(ProcessNextExecutionUseCase):
    """Claim and process the next queued execution."""

    def __init__(
        self,
        executions: ExecutionPersistencePort,
        results: ExecutionResultsPersistencePort,
        plans: TestPlanPersistencePort,
        test_sets: TestSetPersistencePort,
        test_cases: TestCasePersistencePort,
        preconditions: PreconditionPersistencePort,
        compiler: DefinitionCompiler,
        runner: RunnerPort,
        cancellations: ExecutionCancellationPort,
    ) -> None:
        self._executions = executions
        self._results = results
        self._plans = plans
        self._test_sets = test_sets
        self._test_cases = test_cases
        self._preconditions = preconditions
        self._compiler = compiler
        self._runner = runner
        self._cancellations = cancellations

    async def execute(self, _: None) -> Execution | None:
        execution = await self._executions.claim_next_created()

        if execution is None:
            return None
        if execution.runner_version != self._runner.version:
            execution = await self._executions.save_execution(
                replace(
                    execution,
                    runner_version=self._runner.version,
                )
            )

        cancellation = self._cancellations.register(execution.identifier)

        try:
            outcomes = await self._execute(
                execution,
                cancellation,
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
    ) -> tuple[ResultStatus, ...]:
        plan = await self._plans.find_by_id(execution.test_plan_id)

        if plan is None or plan.status is not VersionStatus.ACTIVE:
            raise ValueError("execution plan is no longer active")

        identifiers = list(plan.test_case_ids)

        for test_set_id in plan.test_set_ids:
            test_set = await self._test_sets.find_by_id(test_set_id)

            if test_set is None or test_set.status is not VersionStatus.ACTIVE:
                raise ValueError("execution references an inactive test set")

            identifiers.extend(test_set.items)

        selected = tuple(
            identifier for identifier in identifiers if identifier not in plan.exclusions
        )

        statuses: list[ResultStatus] = []

        for identifier in selected:
            if cancellation.is_set():
                break

            test_case = await self._test_cases.find_by_id(identifier)

            if test_case is None or test_case.status is not VersionStatus.ACTIVE:
                raise ValueError("execution references an inactive test case")

            status = await self._execute_test_case(
                execution,
                test_case,
                cancellation,
            )

            statuses.append(status)

        return tuple(statuses)

    async def _execute_test_case(
        self,
        execution: Execution,
        test_case,
        cancellation: asyncio.Event,
    ) -> ResultStatus:
        started_at = datetime.now(UTC)

        for reference in test_case.preconditions:
            precondition = await self._preconditions.find_by_id(reference.identifier)

            if precondition is None or precondition.status is not VersionStatus.ACTIVE:
                return await self._save_blocked(
                    execution,
                    test_case.identifier,
                    started_at,
                )

            compiled = self._compiler.compile(
                precondition.identifier,
                precondition.validation_definition,
            )

            if not self._runner.supports(frozenset(item.action_type for item in compiled.actions)):
                return await self._save_blocked(
                    execution,
                    test_case.identifier,
                    started_at,
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
                )

        compiled = self._compiler.compile(
            test_case.identifier,
            test_case.definition,
        )

        if not self._runner.supports(frozenset(item.action_type for item in compiled.actions)):
            return await self._save_blocked(
                execution,
                test_case.identifier,
                started_at,
            )

        outcome = await self._runner.execute(
            compiled,
            cancellation,
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
            actions,
        )

        return outcome.status

    async def _save_blocked(
        self,
        execution: Execution,
        test_case_id,
        started_at: datetime,
    ) -> ResultStatus:
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
                "PRECONDITION_FAILED",
                "A required precondition did not pass.",
            ),
            (),
        )

        return ResultStatus.BLOCKED

    @staticmethod
    def _execution_status(
        statuses: tuple[ResultStatus, ...],
    ) -> ExecutionStatus:
        if not statuses:
            return ExecutionStatus.PASSED

        failed = sum(status is not ResultStatus.PASSED for status in statuses)

        if failed == 0:
            return ExecutionStatus.PASSED

        if failed == len(statuses):
            return ExecutionStatus.FAILED

        return ExecutionStatus.PARTIALLY_FAILED
