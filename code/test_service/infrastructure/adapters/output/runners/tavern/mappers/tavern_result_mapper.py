"""Translation from Tavern technical results to the RunnerPort contract."""

from dataclasses import replace
from datetime import UTC, datetime

from test_service.domain.model.execution.execution import ResultStatus
from test_service.domain.ports.output.runners.runner_dtos import (
    CompiledAction,
    RunnerActionOutcome,
)
from test_service.infrastructure.adapters.output.runners.tavern.dtos.tavern_dtos import (
    TavernExecutionResult,
)


class TavernResultMapper:
    """Map structured Tavern records to normalized runner outcomes."""

    def map(
        self, actions: tuple[CompiledAction, ...], result: TavernExecutionResult
    ) -> tuple[RunnerActionOutcome, ...]:
        """Return one normalized outcome per input action in its original order."""
        stages = {stage.identifier: stage for stage in result.stages}
        outcomes: list[RunnerActionOutcome] = []
        failed = False
        now = datetime.now(UTC)
        for action in actions:
            stage = stages.get(action.identifier)
            if stage is not None:
                status = ResultStatus(stage.status)
                outcomes.append(
                    RunnerActionOutcome(
                        action.identifier,
                        action.action_type,
                        status,
                        stage.started_at,
                        stage.finished_at,
                        stage.expected,
                        stage.actual,
                        error_code=stage.error_code,
                        error_message=stage.error_message,
                    )
                )
                failed = failed or status is not ResultStatus.PASSED
                continue
            outcome = self._missing_stage(action, now, result.cancelled, failed, result.exit_code)
            outcomes.append(outcome)
            failed = failed or outcome.status is not ResultStatus.PASSED
        if result.exit_code != 0 and all(
            outcome.status is ResultStatus.PASSED for outcome in outcomes
        ):
            outcomes[-1] = _process_error(outcomes[-1], result.exit_code)
        return tuple(outcomes)

    @staticmethod
    def _missing_stage(
        action: CompiledAction,
        timestamp: datetime,
        cancelled: bool,
        failed: bool,
        exit_code: int,
    ) -> RunnerActionOutcome:
        """Represent cancellation, fail-fast skips, or an invalid missing stage result."""
        if cancelled:
            return _skipped(action, timestamp, "CANCELLED", "Tavern process cancelled")
        if failed:
            return _skipped(
                action,
                timestamp,
                "TAVERN_STAGE_NOT_EXECUTED",
                "A previous Tavern stage failed",
            )
        if exit_code != 0:
            return _error(
                action,
                timestamp,
                "TAVERN_PROCESS_FAILED",
                f"Tavern process exited with code {exit_code} before reporting this stage",
            )
        return _error(
            action,
            timestamp,
            "TAVERN_RESULT_MISSING",
            "Tavern did not emit a structured stage result",
        )


def _failed(
    action: CompiledAction, started_at: datetime, code: str, message: str
) -> RunnerActionOutcome:
    """Build a normalized failed outcome for a runner action."""
    return RunnerActionOutcome(
        action.identifier,
        action.action_type,
        ResultStatus.FAILED,
        started_at,
        datetime.now(UTC),
        error_code=code,
        error_message=message,
    )


def _error(
    action: CompiledAction, started_at: datetime, code: str, message: str
) -> RunnerActionOutcome:
    """Build a normalized runner-error outcome for an action that did not start."""
    return RunnerActionOutcome(
        action.identifier,
        action.action_type,
        ResultStatus.ERROR,
        started_at,
        datetime.now(UTC),
        error_code=code,
        error_message=message,
    )


def _process_error(outcome: RunnerActionOutcome, exit_code: int) -> RunnerActionOutcome:
    """Replace a passed terminal stage when Tavern itself exits unsuccessfully."""
    return replace(
        outcome,
        status=ResultStatus.ERROR,
        error_code="TAVERN_PROCESS_FAILED",
        error_message=f"Tavern process exited with code {exit_code}",
    )


def _skipped(
    action: CompiledAction, timestamp: datetime, code: str, message: str
) -> RunnerActionOutcome:
    """Build a normalized skipped outcome for a runner action."""
    return RunnerActionOutcome(
        action.identifier,
        action.action_type,
        ResultStatus.SKIPPED,
        timestamp,
        timestamp,
        error_code=code,
        error_message=message,
    )
