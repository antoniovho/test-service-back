import asyncio
from datetime import UTC, datetime

import pytest

from test_service.domain.model.execution.execution import ResultStatus
from test_service.domain.ports.output.runners.runner_dtos import (
    CompiledAction,
    CompiledTestCase,
    ExecutionSubjectType,
    RunnerActionOutcome,
)
from test_service.infrastructure.adapters.output.runners.tavern.dtos.tavern_dtos import (
    TavernExecutionResult,
)
from test_service.infrastructure.adapters.output.runners.tavern.tavern_exceptions import (
    TavernResultInvalidError,
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


class _RecordingCompiler:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[str, ...], dict[str, str]]] = []

    def compile(self, actions, context):
        self.calls.append((tuple(action.identifier for action in actions), dict(context)))
        return {"actions": tuple(action.identifier for action in actions)}


class _RecordingExecutor:
    def __init__(self, results: list[TavernExecutionResult]) -> None:
        self._results = results
        self.calls: list[tuple[dict[str, tuple[str, ...]], tuple[str, ...]]] = []

    async def execute(self, document, stage_identifiers, cancellation):
        self.calls.append((document, stage_identifiers))
        return self._results.pop(0)


class _AllPassingResultMapper:
    def map(self, actions, result):
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        return tuple(
            RunnerActionOutcome(
                action.identifier,
                action.action_type,
                ResultStatus.PASSED,
                timestamp,
                timestamp,
            )
            for action in actions
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


class _FailingSseExecutor:
    async def execute(self, client, action, context, cancellation):
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        return RunnerActionOutcome(
            action.identifier,
            action.action_type,
            ResultStatus.ERROR,
            timestamp,
            timestamp,
            error_code="SSE_TRANSPORT_ERROR",
            error_message="SSE stream could not be opened",
        )


class _RecordingSseExecutor:
    def __init__(self, cancellation: asyncio.Event | None = None) -> None:
        self._cancellation = cancellation
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def execute(self, client, action, context, cancellation):
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        self.calls.append((action.identifier, dict(context)))
        if self._cancellation is not None:
            self._cancellation.set()
        return RunnerActionOutcome(
            action.identifier,
            action.action_type,
            ResultStatus.PASSED,
            timestamp,
            timestamp,
        )


class _FailingResultMapper:
    def map(self, actions, result):
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        return (
            RunnerActionOutcome(
                actions[0].identifier,
                actions[0].action_type,
                ResultStatus.FAILED,
                timestamp,
                timestamp,
                error_code="ASSERTION_FAILED",
                error_message="Expected response did not match",
            ),
        )


class _FailingCompiler:
    def compile(self, actions, context):
        raise ValueError("invalid HTTP action")


class _RaisingCompiler:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def compile(self, actions, context):
        raise self._error


class _MalformedExecutor:
    async def execute(self, document, stage_identifiers, cancellation):
        raise TavernResultInvalidError("Tavern result report is invalid")


class _VariableExecutor:
    async def execute(self, document, stage_identifiers, cancellation):
        return TavernExecutionResult(0, False, (), {"sessionToken": "saved-token"})


class _CancellingVariableExecutor:
    async def execute(self, document, stage_identifiers, cancellation):
        cancellation.set()
        return TavernExecutionResult(0, False, (), {"sessionToken": "saved-token"})


class TestTavernRunnerAdapter:
    @pytest.mark.parametrize(
        ("action_types", "expected"),
        [
            (frozenset(), True),
            (frozenset({"HTTP"}), True),
            (frozenset({"SSE"}), True),
            (frozenset({"HTTP", "SSE"}), True),
            (frozenset({"HTTP", "WEBSOCKET"}), False),
        ],
        ids=["empty", "http", "sse", "http-and-sse", "unsupported-type"],
    )
    def test_when_action_types_are_requested_expect_only_http_and_sse_supported(
        self, action_types: frozenset[str], expected: bool
    ) -> None:
        adapter = TavernRunnerAdapter()

        supported = adapter.supports(action_types)

        assert supported is expected

    async def test_when_http_block_returns_runner_error_expect_error_test_case_outcome(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        adapter = TavernRunnerAdapter(_Compiler(), _Executor(), _ResultMapper())
        test_case = CompiledTestCase(
            "precondition-id",
            {},
            (CompiledAction("proxyReadiness", "HTTP", 0, {}),),
            ExecutionSubjectType.PRECONDITION,
        )

        outcome = await adapter.execute(test_case, asyncio.Event())

        assert outcome.status is ResultStatus.ERROR
        assert outcome.error_code == "TAVERN_PROCESS_FAILED"
        assert outcome.error_message == (
            "Tavern process exited with code 2 before reporting this stage"
        )
        assert outcome.started_at.tzinfo is UTC
        assert outcome.finished_at.tzinfo is UTC
        assert outcome.actions[0].action_id == "proxyReadiness"
        assert outcome.actions[0].action_type == "HTTP"
        assert "precondition 'precondition-id' stopped at action 'proxyReadiness'" in caplog.text
        assert "TAVERN_PROCESS_FAILED" in caplog.text
        assert "Tavern process exited with code 2" in caplog.text

    async def test_when_cancelled_before_execution_expect_skipped_test_case_outcome(self) -> None:
        cancellation = asyncio.Event()
        cancellation.set()
        test_case = CompiledTestCase("case-id", {}, (CompiledAction("first", "HTTP", 0, {}),))

        outcome = await TavernRunnerAdapter().execute(test_case, cancellation)

        assert outcome.status is ResultStatus.SKIPPED
        assert outcome.error_code == "CANCELLED"
        assert outcome.error_message == "Cancelled"
        assert outcome.actions == ()
        assert outcome.variables == {}
        assert outcome.started_at.tzinfo is UTC
        assert outcome.finished_at.tzinfo is UTC

    async def test_when_cancelled_after_http_block_expect_skipped_outcome_with_saved_variables(
        self,
    ) -> None:
        adapter = TavernRunnerAdapter(
            _Compiler(), _CancellingVariableExecutor(), _PassingResultMapper()
        )
        test_case = CompiledTestCase("case-id", {}, (CompiledAction("first", "HTTP", 0, {}),))

        outcome = await adapter.execute(test_case, asyncio.Event())

        assert outcome.status is ResultStatus.SKIPPED
        assert outcome.error_code == "CANCELLED"
        assert outcome.error_message == "Cancelled"
        assert outcome.started_at is not None
        assert outcome.finished_at is not None
        assert outcome.variables == {"sessionToken": "saved-token"}

    async def test_when_sse_action_passes_expect_passed_test_case_outcome(self) -> None:
        adapter = TavernRunnerAdapter(sse_executor=_SseExecutor())
        test_case = CompiledTestCase("case-id", {}, (CompiledAction("first", "SSE", 0, {}),))

        outcome = await adapter.execute(test_case, asyncio.Event())

        assert outcome.status is ResultStatus.PASSED
        assert outcome.actions[0].status is ResultStatus.PASSED

    async def test_when_sse_action_errors_expect_later_actions_not_executed(self) -> None:
        compiler = _RecordingCompiler()
        adapter = TavernRunnerAdapter(compiler=compiler, sse_executor=_FailingSseExecutor())
        test_case = CompiledTestCase(
            "case-id",
            {},
            (
                CompiledAction("failing-event", "SSE", 0, {}),
                CompiledAction("later-http", "HTTP", 1, {}),
            ),
        )

        outcome = await adapter.execute(test_case, asyncio.Event())

        assert outcome.status is ResultStatus.ERROR
        assert outcome.error_code == "SSE_TRANSPORT_ERROR"
        assert outcome.error_message == "SSE stream could not be opened"
        assert [action.action_id for action in outcome.actions] == ["failing-event"]
        assert compiler.calls == []

    async def test_when_compiled_test_case_has_no_actions_expect_empty_passed_outcome(self) -> None:
        test_case = CompiledTestCase("case-id", {"tenant": "acme"}, ())

        outcome = await TavernRunnerAdapter().execute(test_case, asyncio.Event())

        assert outcome.status is ResultStatus.PASSED
        assert outcome.actions == ()
        assert outcome.error_code is None
        assert outcome.error_message is None
        assert outcome.variables == {}

    async def test_when_http_blocks_are_separated_by_sse_expect_grouping_order_and_context(
        self,
    ) -> None:
        compiler = _RecordingCompiler()
        executor = _RecordingExecutor(
            [
                TavernExecutionResult(0, False, (), {"sessionToken": "saved-token"}),
                TavernExecutionResult(0, False, (), {"profileId": "profile-42"}),
            ]
        )
        sse_executor = _RecordingSseExecutor()
        adapter = TavernRunnerAdapter(compiler, executor, _AllPassingResultMapper(), sse_executor)
        test_case = CompiledTestCase(
            "case-id",
            {"requestId": "request-7"},
            (
                CompiledAction("login", "HTTP", 0, {}),
                CompiledAction("catalog", "HTTP", 1, {}),
                CompiledAction("inventory-event", "SSE", 2, {}),
                CompiledAction("profile", "HTTP", 3, {}),
                CompiledAction("preferences", "HTTP", 4, {}),
            ),
        )

        outcome = await adapter.execute(test_case, asyncio.Event())

        assert outcome.status is ResultStatus.PASSED
        assert [action.action_id for action in outcome.actions] == [
            "login",
            "catalog",
            "inventory-event",
            "profile",
            "preferences",
        ]
        assert outcome.variables == {"sessionToken": "saved-token", "profileId": "profile-42"}
        assert compiler.calls == [
            (("login", "catalog"), {"requestId": "request-7"}),
            (
                ("profile", "preferences"),
                {"requestId": "request-7", "sessionToken": "saved-token"},
            ),
        ]
        assert executor.calls == [
            ({"actions": ("login", "catalog")}, ("login", "catalog")),
            ({"actions": ("profile", "preferences")}, ("profile", "preferences")),
        ]
        assert sse_executor.calls == [
            ("inventory-event", {"requestId": "request-7", "sessionToken": "saved-token"})
        ]

    async def test_when_http_action_fails_expect_later_actions_not_executed(self) -> None:
        compiler = _RecordingCompiler()
        executor = _RecordingExecutor([TavernExecutionResult(0, False, (), {})])
        sse_executor = _RecordingSseExecutor()
        adapter = TavernRunnerAdapter(compiler, executor, _FailingResultMapper(), sse_executor)
        test_case = CompiledTestCase(
            "case-id",
            {},
            (
                CompiledAction("failing-http", "HTTP", 0, {}),
                CompiledAction("later-event", "SSE", 1, {}),
            ),
        )

        outcome = await adapter.execute(test_case, asyncio.Event())

        assert outcome.status is ResultStatus.FAILED
        assert outcome.error_code == "ASSERTION_FAILED"
        assert outcome.error_message == "Expected response did not match"
        assert [action.action_id for action in outcome.actions] == ["failing-http"]
        assert compiler.calls == [(("failing-http",), {})]
        assert sse_executor.calls == []

    async def test_when_cancelled_after_sse_expect_later_http_block_not_executed(self) -> None:
        cancellation = asyncio.Event()
        compiler = _RecordingCompiler()
        executor = _RecordingExecutor([])
        sse_executor = _RecordingSseExecutor(cancellation)
        adapter = TavernRunnerAdapter(compiler, executor, _AllPassingResultMapper(), sse_executor)
        test_case = CompiledTestCase(
            "case-id",
            {},
            (
                CompiledAction("event", "SSE", 0, {}),
                CompiledAction("later-http", "HTTP", 1, {}),
            ),
        )

        outcome = await adapter.execute(test_case, cancellation)

        assert outcome.status is ResultStatus.SKIPPED
        assert outcome.error_code == "CANCELLED"
        assert outcome.error_message == "Cancelled"
        assert [action.action_id for action in outcome.actions] == ["event"]
        assert compiler.calls == []

    async def test_when_http_compilation_fails_expect_error_action_outcome(self) -> None:
        adapter = TavernRunnerAdapter(compiler=_FailingCompiler())
        action = CompiledAction("first", "HTTP", 0, {})

        outcomes, variables = await adapter._tavern_http_block((action,), {}, asyncio.Event())

        assert outcomes[0].status is ResultStatus.ERROR
        assert outcomes[0].error_code == "TAVERN_RUNNER_ERROR"
        assert outcomes[0].action_id == "first"
        assert outcomes[0].action_type == "HTTP"
        assert outcomes[0].started_at.tzinfo is UTC
        assert outcomes[0].finished_at.tzinfo is UTC
        assert variables == {}

    async def test_when_runner_error_is_caught_expect_safe_diagnostic_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        adapter = TavernRunnerAdapter(compiler=_RaisingCompiler(ValueError("secret details")))
        action = CompiledAction("first", "HTTP", 0, {})

        await adapter._tavern_http_block((action,), {}, asyncio.Event())

        assert "Tavern runner failed while preparing HTTP actions ['first']" in caplog.text
        assert "ValueError while compiling or starting Tavern" in caplog.text
        assert "secret details" not in caplog.text

    async def test_when_runner_rejects_unsafe_document_expect_safe_cause_in_outcome(
        self,
    ) -> None:
        adapter = TavernRunnerAdapter(
            compiler=_RaisingCompiler(
                ValueError("HTTP action 'first' uses template field 'tavern.env_vars.SECRET'")
            )
        )
        action = CompiledAction("first", "HTTP", 0, {})

        outcomes, _ = await adapter._tavern_http_block((action,), {}, asyncio.Event())

        assert outcomes[0].error_message == (
            "Tavern failed before receiving an HTTP response: HTTP action 'first' uses "
            "template field 'tavern.env_vars.SECRET'"
        )

    async def test_when_tavern_saves_variables_expect_variables_returned_in_outcome(self) -> None:
        adapter = TavernRunnerAdapter(_Compiler(), _VariableExecutor(), _PassingResultMapper())
        test_case = CompiledTestCase("case-id", {}, (CompiledAction("first", "HTTP", 0, {}),))

        outcome = await adapter.execute(test_case, asyncio.Event())

        assert outcome.variables == {"sessionToken": "saved-token"}

    async def test_when_tavern_report_is_malformed_expect_invalid_result_error(self) -> None:
        adapter = TavernRunnerAdapter(executor=_MalformedExecutor())
        action = CompiledAction("first", "HTTP", 0, {})

        outcomes, variables = await adapter._tavern_http_block((action,), {}, asyncio.Event())

        assert outcomes[0].status is ResultStatus.ERROR
        assert outcomes[0].error_code == "TAVERN_RESULT_INVALID"
        assert outcomes[0].error_message == "Tavern result report is invalid"
        assert variables == {}

    @pytest.mark.parametrize(
        "error",
        [OSError("socket details"), TypeError("internal details"), ValueError("secret details")],
        ids=["os-error", "type-error", "value-error"],
    )
    async def test_when_runner_error_is_raised_expect_normalized_error_for_each_http_action(
        self, error: Exception
    ) -> None:
        adapter = TavernRunnerAdapter(compiler=_RaisingCompiler(error))
        actions = (
            CompiledAction("first", "HTTP", 0, {}),
            CompiledAction("second", "HTTP", 1, {}),
        )

        outcomes, variables = await adapter._tavern_http_block(actions, {}, asyncio.Event())

        assert [outcome.status for outcome in outcomes] == [ResultStatus.ERROR, ResultStatus.ERROR]
        assert [outcome.error_code for outcome in outcomes] == [
            "TAVERN_RUNNER_ERROR",
            "TAVERN_RUNNER_ERROR",
        ]
        expected_message = (
            "Tavern failed before receiving an HTTP response: "
            f"{type(error).__name__} while compiling or starting Tavern"
        )
        assert [outcome.error_message for outcome in outcomes] == [
            expected_message,
            expected_message,
        ]
        assert [outcome.action_id for outcome in outcomes] == ["first", "second"]
        assert [outcome.action_type for outcome in outcomes] == ["HTTP", "HTTP"]
        assert all(outcome.started_at.tzinfo is UTC for outcome in outcomes)
        assert all(outcome.finished_at.tzinfo is UTC for outcome in outcomes)
        assert "details" not in str(outcomes)
        assert variables == {}

    def test_when_building_test_case_outcome_expect_all_supplied_fields_preserved(self) -> None:
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        action = RunnerActionOutcome("request", "HTTP", ResultStatus.PASSED, timestamp, timestamp)

        outcome = TavernRunnerAdapter._build_test_case_outcome(
            ResultStatus.ERROR,
            timestamp,
            [action],
            "PARTIAL_FAILURE",
            "One action failed",
            {"session": "saved"},
        )

        assert outcome.status is ResultStatus.ERROR
        assert outcome.started_at == timestamp
        assert outcome.finished_at.tzinfo is UTC
        assert outcome.actions == (action,)
        assert outcome.error_code == "PARTIAL_FAILURE"
        assert outcome.error_message == "One action failed"
        assert outcome.variables == {"session": "saved"}
