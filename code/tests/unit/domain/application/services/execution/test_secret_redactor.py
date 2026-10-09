from datetime import UTC, datetime

import pytest

from test_service.domain.application.services.execution.secret_redactor import (
    REDACTED,
    redact_test_case_outcome,
)
from test_service.domain.model.execution.execution import ResultStatus
from test_service.domain.ports.output.runners.runner_dtos import (
    RunnerActionOutcome,
    RunnerTestCaseOutcome,
)

_AT = datetime(2026, 1, 1, tzinfo=UTC)


def _action(**overrides: object) -> RunnerActionOutcome:
    fields = {
        "action_id": "request",
        "action_type": "HTTP",
        "status": ResultStatus.FAILED,
        "started_at": _AT,
        "finished_at": _AT,
    }
    fields.update(overrides)
    return RunnerActionOutcome(**fields)


def _outcome(*actions: RunnerActionOutcome, **overrides: object) -> RunnerTestCaseOutcome:
    fields = {"status": ResultStatus.FAILED, "started_at": _AT, "finished_at": _AT}
    fields.update(overrides)
    return RunnerTestCaseOutcome(actions=actions, **fields)


class TestRedactTestCaseOutcome:
    @pytest.mark.parametrize(
        "secrets", [(), frozenset(), ("",)], ids=["tuple", "set", "empty-text"]
    )
    def test_when_there_is_nothing_to_redact_expect_same_outcome(self, secrets) -> None:
        outcome = _outcome(_action(actual={"token": "visible"}))

        redacted = redact_test_case_outcome(outcome, secrets)

        assert redacted is outcome

    def test_when_secret_is_in_action_evidence_expect_it_replaced_everywhere(self) -> None:
        action = _action(
            expected={"header": "Bearer s3cr3t"},
            actual={
                "request": {
                    "url": "https://api.test/?k=s3cr3t",
                    "headers": {"X-Custom-Token": "s3cr3t", "X-Trace": "trace"},
                },
                "events": ["a s3cr3t b", {"data": "s3cr3t"}],
            },
            output={"saved": "s3cr3t"},
            error_message="rejected s3cr3t twice: s3cr3t",
        )

        redacted = redact_test_case_outcome(_outcome(action), {"s3cr3t"})

        result = redacted.actions[0]
        assert result.expected == {"header": f"Bearer {REDACTED}"}
        assert result.actual == {
            "request": {
                "url": f"https://api.test/?k={REDACTED}",
                "headers": {"X-Custom-Token": REDACTED, "X-Trace": "trace"},
            },
            "events": [f"a {REDACTED} b", {"data": REDACTED}],
        }
        assert result.output == {"saved": REDACTED}
        assert result.error_message == f"rejected {REDACTED} twice: {REDACTED}"

    def test_when_secret_is_in_test_case_error_message_expect_it_replaced(self) -> None:
        outcome = _outcome(_action(), error_message="token s3cr3t failed")

        redacted = redact_test_case_outcome(outcome, {"s3cr3t"})

        assert redacted.error_message == f"token {REDACTED} failed"

    def test_when_secret_is_a_mapping_key_expect_key_replaced(self) -> None:
        outcome = _outcome(_action(actual={"s3cr3t": "value"}))

        redacted = redact_test_case_outcome(outcome, {"s3cr3t"})

        assert redacted.actions[0].actual == {REDACTED: "value"}

    def test_when_one_secret_contains_another_expect_longest_removed_first(self) -> None:
        outcome = _outcome(_action(actual={"value": "abcdef"}))

        redacted = redact_test_case_outcome(outcome, {"abc", "abcdef"})

        assert redacted.actions[0].actual == {"value": REDACTED}

    def test_when_value_is_not_text_expect_it_unchanged(self) -> None:
        action = _action(actual={"status": 200, "ok": True, "missing": None, "ratio": 0.5})

        redacted = redact_test_case_outcome(_outcome(action), {"s3cr3t"})

        assert redacted.actions[0].actual == {
            "status": 200,
            "ok": True,
            "missing": None,
            "ratio": 0.5,
        }

    def test_when_fields_are_absent_expect_them_kept_as_none(self) -> None:
        outcome = _outcome(_action(), error_message=None)

        redacted = redact_test_case_outcome(outcome, {"s3cr3t"})

        assert redacted.actions[0].expected is None
        assert redacted.actions[0].error_message is None
        assert redacted.error_message is None

    def test_when_redacting_expect_original_outcome_untouched(self) -> None:
        action = _action(actual={"token": "s3cr3t"}, error_message="s3cr3t")
        outcome = _outcome(action, error_message="s3cr3t")

        redact_test_case_outcome(outcome, {"s3cr3t"})

        assert outcome.actions[0].actual == {"token": "s3cr3t"}
        assert outcome.actions[0].error_message == "s3cr3t"
        assert outcome.error_message == "s3cr3t"

    def test_when_redacting_expect_non_text_fields_preserved(self) -> None:
        action = _action(error_code="TAVERN_ASSERTION_FAILED", status=ResultStatus.FAILED)
        outcome = _outcome(action, error_code="TAVERN_ASSERTION_FAILED")

        redacted = redact_test_case_outcome(outcome, {"s3cr3t"})

        assert redacted.status is ResultStatus.FAILED
        assert redacted.error_code == "TAVERN_ASSERTION_FAILED"
        assert redacted.actions[0].error_code == "TAVERN_ASSERTION_FAILED"
        assert redacted.actions[0].started_at == _AT
