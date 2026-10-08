import asyncio
from datetime import UTC, datetime

from test_service.domain.model.execution.execution import ResultStatus
from test_service.domain.ports.output.runners.runner_dtos import (
    CompiledAction,
    CompiledTestCase,
    RunnerActionOutcome,
)
from test_service.infrastructure.adapters.output.runners.tavern.dtos.tavern_dtos import (
    TavernExecutionResult,
)
from test_service.infrastructure.adapters.output.runners.tavern.tavern_runner_adapter import (
    TavernRunnerAdapter,
)


class _Compiler:
    def compile(self, actions, context):
        return {}


class _Executor:
    async def execute(self, document, stage_identifiers, cancellation):
        return TavernExecutionResult(2, False, (), {})


class _ResultMapper:
    def map(self, actions, result):
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        return (
            RunnerActionOutcome(
                actions[0].identifier,
                actions[0].action_type,
                ResultStatus.ERROR,
                timestamp,
                timestamp,
                error_code="TAVERN_PROCESS_FAILED",
                error_message="Tavern process exited with code 2 before reporting this stage",
            ),
        )


class _PassingResultMapper:
    def map(self, actions, result):
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        return (
            RunnerActionOutcome(
                actions[0].identifier,
                actions[0].action_type,
                ResultStatus.PASSED,
                timestamp,
                timestamp,
            ),
        )


class _SseExecutor:
    async def execute(self, client, action, context, cancellation):
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        return RunnerActionOutcome(
            action.identifier,
            action.action_type,
            ResultStatus.PASSED,
            timestamp,
            timestamp,
        )


class _FailingCompiler:
    def compile(self, actions, context):
        raise ValueError("invalid HTTP action")


class TestTavernRunnerAdapter:
    async def test_when_http_block_returns_runner_error_expect_error_test_case_outcome(
        self,
    ) -> None:
        adapter = TavernRunnerAdapter(_Compiler(), _Executor(), _ResultMapper())
        test_case = CompiledTestCase("case-id", {}, (CompiledAction("first", "HTTP", 0, {}),))

        outcome = await adapter.execute(test_case, asyncio.Event())

        assert outcome.status is ResultStatus.ERROR
        assert outcome.error_code == "TAVERN_PROCESS_FAILED"

    async def test_when_cancelled_before_execution_expect_skipped_test_case_outcome(self) -> None:
        cancellation = asyncio.Event()
        cancellation.set()
        test_case = CompiledTestCase("case-id", {}, (CompiledAction("first", "HTTP", 0, {}),))

        outcome = await TavernRunnerAdapter().execute(test_case, cancellation)

        assert outcome.status is ResultStatus.SKIPPED
        assert outcome.error_code == "CANCELLED"

    async def test_when_sse_action_passes_expect_passed_test_case_outcome(self) -> None:
        adapter = TavernRunnerAdapter(sse_executor=_SseExecutor())
        test_case = CompiledTestCase("case-id", {}, (CompiledAction("first", "SSE", 0, {}),))

        outcome = await adapter.execute(test_case, asyncio.Event())

        assert outcome.status is ResultStatus.PASSED
        assert outcome.actions[0].status is ResultStatus.PASSED

    async def test_when_http_compilation_fails_expect_failed_action_outcome(self) -> None:
        adapter = TavernRunnerAdapter(compiler=_FailingCompiler())
        action = CompiledAction("first", "HTTP", 0, {})

        outcomes, variables = await adapter._tavern_http_block((action,), {}, asyncio.Event())

        assert outcomes[0].status is ResultStatus.FAILED
        assert outcomes[0].error_code == "TAVERN_RUNNER_ERROR"
        assert variables == {}
