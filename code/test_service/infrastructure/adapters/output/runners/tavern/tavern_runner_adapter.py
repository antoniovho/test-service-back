"""Tavern-backed HTTP runner with a bounded SSE extension.

Tavern's HTTP backend is invoked through its supported ``tavern-ci`` CLI. A
separate process gives every test an isolation boundary and lets cancellation
terminate the active request. Tavern has no SSE backend, so SSE remains an
infrastructure extension of this adapter rather than a domain concern.
"""

import asyncio
import logging
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
from test_service.infrastructure.adapters.output.runners.sse.sse_action_executor import (
    SseExecutor,
)
from test_service.infrastructure.adapters.output.runners.tavern.compilers.tavern_compiler import (
    TavernCompiler,
)
from test_service.infrastructure.adapters.output.runners.tavern.executors.tavern_executor import (
    TavernExecutor,
)
from test_service.infrastructure.adapters.output.runners.tavern.mappers.tavern_result_mapper import (  # noqa: E501
    TavernResultMapper,
)
from test_service.infrastructure.adapters.output.runners.tavern.tavern_exceptions import (
    TavernResultInvalidError,
)

logger = logging.getLogger(__name__)


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
        saved_variables: dict[str, str] = {}
        outcomes: list[RunnerActionOutcome] = []
        async with httpx.AsyncClient() as client:
            index = 0
            while index < len(test_case.actions):
                if cancellation.is_set():
                    return self._build_test_case_outcome(
                        ResultStatus.SKIPPED,
                        started_at,
                        outcomes,
                        "CANCELLED",
                        "Cancelled",
                        saved_variables,
                    )
                action = test_case.actions[index]
                if action.action_type == "HTTP":
                    block, index = self._http_block(test_case.actions, index)
                    block_outcomes, variables = await self._tavern_http_block(
                        block, context, cancellation
                    )
                    outcomes.extend(block_outcomes)
                    context.update(variables)
                    saved_variables.update(variables)
                else:
                    outcome = await self._sse_executor.execute(
                        client, action, context, cancellation
                    )
                    outcomes.append(outcome)
                    index += 1
                if cancellation.is_set():
                    return self._build_test_case_outcome(
                        ResultStatus.SKIPPED,
                        started_at,
                        outcomes,
                        "CANCELLED",
                        "Cancelled",
                        saved_variables,
                    )
                terminal_issue = next(
                    (
                        item
                        for item in outcomes
                        if item.status in {ResultStatus.FAILED, ResultStatus.ERROR}
                    ),
                    None,
                )
                if terminal_issue is not None:
                    self._log_terminal_issue(test_case.test_case_id, terminal_issue)
                    return self._build_test_case_outcome(
                        terminal_issue.status,
                        started_at,
                        outcomes,
                        terminal_issue.error_code,
                        terminal_issue.error_message,
                        saved_variables,
                    )
        return self._build_test_case_outcome(
            ResultStatus.PASSED, started_at, outcomes, variables=saved_variables
        )

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
        except TavernResultInvalidError:
            logger.warning(
                "Tavern emitted an invalid result report for HTTP actions %s.",
                [action.identifier for action in actions],
            )
            return (
                tuple(
                    self._error(
                        action,
                        started_at,
                        "TAVERN_RESULT_INVALID",
                        "Tavern result report is invalid",
                    )
                    for action in actions
                ),
                {},
            )
        except (OSError, TypeError, ValueError) as exc:
            error = self._runner_error_message(exc)
            logger.warning(
                "Tavern runner failed while preparing HTTP actions %s: %s",
                [action.identifier for action in actions],
                error,
            )
            return (
                tuple(
                    self._error(
                        action,
                        started_at,
                        "TAVERN_RUNNER_ERROR",
                        error,
                    )
                    for action in actions
                ),
                {},
            )

    @staticmethod
    def _runner_error_message(error: OSError | TypeError | ValueError) -> str:
        """Build a diagnostic for failures that happen before an HTTP response.

        Tavern compilation can render service variables, including secrets. We
        therefore disclose only error text produced by this adapter's fixed
        validation rules; arbitrary exception text is reduced to its type.
        """
        prefix = "Tavern failed before receiving an HTTP response"
        if isinstance(error, FileNotFoundError):
            return f"{prefix}: tavern-ci executable was not found"
        if isinstance(error, PermissionError):
            return f"{prefix}: tavern-ci could not be executed"

        message = str(error)
        safe_prefixes = (
            "HTTP action configuration must be an object",
            "HTTP action '",
            "Tavern document uses ",
            "expectedJsonSchema must be an object",
        )
        if isinstance(error, ValueError) and message.startswith(safe_prefixes):
            return f"{prefix}: {message}"
        return f"{prefix}: {type(error).__name__} while compiling or starting Tavern"

    @staticmethod
    def _log_terminal_issue(test_case_id: str, outcome: RunnerActionOutcome) -> None:
        """Expose a normalized action failure in the application log.

        ``error_message`` is the same sanitized and bounded diagnostic that is
        persisted in the result API; logging it makes asynchronous executions
        observable without adding a separate runner console.
        """
        logger.warning(
            "Execution of test case '%s' stopped at action '%s' with status %s (code: %s): %s",
            test_case_id,
            outcome.action_id,
            outcome.status.value,
            outcome.error_code or "UNKNOWN",
            outcome.error_message or "No diagnostic was reported",
        )

    @staticmethod
    def _error(action, started_at, code, error):
        """Build an error action outcome without exposing exception contents."""
        return RunnerActionOutcome(
            action.identifier,
            action.action_type,
            ResultStatus.ERROR,
            started_at,
            datetime.now(UTC),
            error_code=code,
            error_message=error,
        )

    @staticmethod
    def _build_test_case_outcome(
        status, started_at, actions, code=None, message=None, variables=None
    ):
        """Build the aggregate result for a compiled Test Case."""
        return RunnerTestCaseOutcome(
            status,
            started_at,
            datetime.now(UTC),
            tuple(actions),
            code,
            message,
            variables or {},
        )
