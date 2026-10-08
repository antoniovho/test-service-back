"""Tavern-backed HTTP runner with a bounded SSE extension.

Tavern's HTTP backend is invoked through its supported ``tavern-ci`` CLI. A
separate process gives every test an isolation boundary and lets cancellation
terminate the active request. Tavern has no SSE backend, so SSE remains an
infrastructure extension of this adapter rather than a domain concern.
"""

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime

import httpx

from test_service.domain.model.execution.execution import ResultStatus
from test_service.domain.ports.output.runners.runner_dtos import (
    CompiledAction,
    CompiledTestCase,
    RunnerActionOutcome,
    RunnerTestCaseOutcome,
)
from test_service.infrastructure.adapters.output.runners.tavern.compilers.tavern_compiler import (
    TavernCompiler,
)
from test_service.infrastructure.adapters.output.runners.tavern.executors.sse_executor import (
    SseExecutor,
)
from test_service.infrastructure.adapters.output.runners.tavern.executors.tavern_executor import (
    TavernExecutor,
)
from test_service.infrastructure.adapters.output.runners.tavern.mappers.tavern_result_mapper import (  # noqa: E501
    TavernResultMapper,
)


class TavernRunnerAdapter:
    """Run HTTP actions in Tavern and SSE actions using the adapter extension."""

    identifier = "tavern"
    version = "tavern-cli-v3+sse-v1"

    def __init__(
        self,
        compiler: TavernCompiler | None = None,
        executor: TavernExecutor | None = None,
        result_mapper: TavernResultMapper | None = None,
        sse_executor: SseExecutor | None = None,
    ) -> None:
        """Create the adapter with replaceable Tavern infrastructure collaborators."""
        self._compiler = compiler or TavernCompiler()
        self._executor = executor or TavernExecutor()
        self._result_mapper = result_mapper or TavernResultMapper()
        self._sse_executor = sse_executor or SseExecutor()

    def supports(self, action_types: frozenset[str]) -> bool:
        """Report whether this runner can execute every requested action type."""
        return action_types.issubset({"HTTP", "SSE"})

    async def execute(
        self, test_case: CompiledTestCase, cancellation: asyncio.Event
    ) -> RunnerTestCaseOutcome:
        """Execute ordered HTTP blocks and SSE actions with fail-fast semantics."""
        started_at = datetime.now(UTC)
        context = dict(test_case.variables)
        outcomes: list[RunnerActionOutcome] = []
        async with httpx.AsyncClient() as client:
            index = 0
            while index < len(test_case.actions):
                if cancellation.is_set():
                    return self._build_test_case_outcome(
                        ResultStatus.SKIPPED, started_at, outcomes, "CANCELLED", "Cancelled"
                    )
                action = test_case.actions[index]
                if action.action_type == "HTTP":
                    block, index = self._http_block(test_case.actions, index)
                    block_outcomes, variables = await self._tavern_http_block(
                        block, context, cancellation
                    )
                    outcomes.extend(block_outcomes)
                    context.update(variables)
                else:
                    outcome = await self._sse_executor.execute(
                        client, action, context, cancellation
                    )
                    outcomes.append(outcome)
                    index += 1
                if cancellation.is_set():
                    return self._build_test_case_outcome(
                        ResultStatus.SKIPPED, started_at, outcomes, "CANCELLED", "Cancelled"
                    )
                failed = next(
                    (item for item in outcomes if item.status is ResultStatus.FAILED), None
                )
                if failed is not None:
                    return self._build_test_case_outcome(
                        ResultStatus.FAILED,
                        started_at,
                        outcomes,
                        failed.error_code,
                        failed.error_message,
                    )
        return self._build_test_case_outcome(ResultStatus.PASSED, started_at, outcomes)

    @staticmethod
    def _http_block(
        actions: tuple[CompiledAction, ...], index: int
    ) -> tuple[tuple[CompiledAction, ...], int]:
        """Return consecutive HTTP actions starting at the supplied index."""
        end = index
        while end < len(actions) and actions[end].action_type == "HTTP":
            end += 1
        return actions[index:end], end

    async def _tavern_http_block(
        self,
        actions: tuple[CompiledAction, ...],
        context: Mapping[str, str],
        cancellation: asyncio.Event,
    ) -> tuple[tuple[RunnerActionOutcome, ...], Mapping[str, str]]:
        """Execute one consecutive HTTP block as a Tavern multi-stage test."""
        started_at = datetime.now(UTC)
        try:
            document = self._compiler.compile(actions, context)
            result = await self._executor.execute(
                document, tuple(action.identifier for action in actions), cancellation
            )
            return self._result_mapper.map(actions, result), result.variables
        except (OSError, TypeError, ValueError) as exc:
            return (
                tuple(
                    self._failed(action, started_at, "TAVERN_RUNNER_ERROR", error=str(exc))
                    for action in actions
                ),
                {},
            )

    @staticmethod
    def _failed(action, started_at, code, actual=None, error=None):
        """Build a failed action outcome with normalized error information."""
        return RunnerActionOutcome(
            action.identifier,
            action.action_type,
            ResultStatus.FAILED,
            started_at,
            datetime.now(UTC),
            actual=actual,
            error_code=code,
            error_message=error or code.replace("_", " ").lower(),
        )

    @staticmethod
    def _build_test_case_outcome(status, started_at, actions, code=None, message=None):
        """Build the aggregate result for a compiled Test Case."""
        return RunnerTestCaseOutcome(
            status, started_at, datetime.now(UTC), tuple(actions), code, message
        )
