from datetime import UTC, datetime

from test_service.domain.model.execution.execution import ResultStatus
from test_service.domain.ports.output.runners.runner_dtos import CompiledAction
from test_service.infrastructure.adapters.output.runners.tavern.dtos.tavern_dtos import (
    TavernExecutionResult,
    TavernStageResult,
)
from test_service.infrastructure.adapters.output.runners.tavern.mappers.tavern_result_mapper import (  # noqa: E501
    TavernResultMapper,
)


class TestTavernResultMapper:
    def test_when_process_fails_before_stage_reporting_expect_error_and_blocked_actions(
        self,
    ) -> None:
        actions = _http_actions()
        result = TavernExecutionResult(2, False, (), {})

        outcomes = TavernResultMapper().map(actions, result)

        assert [outcome.status for outcome in outcomes] == [
            ResultStatus.ERROR,
            ResultStatus.SKIPPED,
        ]
        assert [outcome.error_code for outcome in outcomes] == [
            "TAVERN_PROCESS_FAILED",
            "TAVERN_STAGE_NOT_EXECUTED",
        ]

    def test_when_successful_process_omits_stage_report_expect_runner_error(self) -> None:
        actions = _http_actions()
        result = TavernExecutionResult(0, False, (), {})

        outcomes = TavernResultMapper().map(actions, result)

        assert outcomes[0].status is ResultStatus.ERROR
        assert outcomes[0].error_code == "TAVERN_RESULT_MISSING"

    def test_when_all_stages_pass_but_process_fails_expect_last_stage_runner_error(
        self,
    ) -> None:
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        result = TavernExecutionResult(
            2,
            False,
            (TavernStageResult("first", "PASSED", timestamp, timestamp),),
            {},
        )

        outcomes = TavernResultMapper().map((CompiledAction("first", "HTTP", 0, {}),), result)

        assert outcomes[0].status is ResultStatus.ERROR
        assert outcomes[0].error_code == "TAVERN_PROCESS_FAILED"


def _http_actions() -> tuple[CompiledAction, ...]:
    return (
        CompiledAction("first", "HTTP", 0, {}),
        CompiledAction("second", "HTTP", 1, {}),
    )
