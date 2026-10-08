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


class TestTavernRunnerAdapter:
    async def test_when_http_block_returns_runner_error_expect_error_test_case_outcome(
        self,
    ) -> None:
        adapter = TavernRunnerAdapter(_Compiler(), _Executor(), _ResultMapper())
        test_case = CompiledTestCase("case-id", {}, (CompiledAction("first", "HTTP", 0, {}),))

        outcome = await adapter.execute(test_case, asyncio.Event())

        assert outcome.status is ResultStatus.ERROR
        assert outcome.error_code == "TAVERN_PROCESS_FAILED"
