"""Map runner outcomes to execution result evidence."""

from uuid import UUID, uuid4

from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.execution.execution import ActionResult
from test_service.domain.ports.output.runners.runner_dtos import (
    RunnerActionOutcome,
    RunnerTestCaseOutcome,
)


class ExecutionResultMapper:
    """Build application-level evidence from runner outcomes."""

    @staticmethod
    def precondition_evidence(
        precondition: Precondition, outcome: RunnerTestCaseOutcome
    ) -> tuple[RunnerActionOutcome, ...]:
        """Represent a precondition result and its actions under the parent test."""
        identifier = str(precondition.identifier)
        summary = RunnerActionOutcome(
            action_id=f"precondition:{identifier}",
            action_type="PRECONDITION",
            status=outcome.status,
            started_at=outcome.started_at,
            finished_at=outcome.finished_at,
            expected={
                "preconditionId": identifier,
                "preconditionKey": precondition.precondition_key,
                "version": precondition.version,
            },
            actual={"actionCount": len(outcome.actions)},
            error_code=outcome.error_code,
            error_message=outcome.error_message,
        )
        actions = tuple(
            RunnerActionOutcome(
                action_id=f"precondition:{identifier}:{action.action_id}",
                action_type=action.action_type,
                status=action.status,
                started_at=action.started_at,
                finished_at=action.finished_at,
                expected=action.expected,
                actual=action.actual,
                output=action.output,
                error_code=action.error_code,
                error_message=action.error_message,
            )
            for action in outcome.actions
        )
        return (summary, *actions)

    @staticmethod
    def to_action_results(
        test_result_id: UUID, outcomes: tuple[RunnerActionOutcome, ...]
    ) -> tuple[ActionResult, ...]:
        """Map normalized runner outcomes into immutable action evidence."""
        return tuple(
            ActionResult(
                identifier=uuid4(),
                test_result_id=test_result_id,
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
            for item in outcomes
        )
