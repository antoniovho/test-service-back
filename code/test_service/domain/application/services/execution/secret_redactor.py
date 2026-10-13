"""Removal of resolved secret values from runner outcomes before they are persisted."""

from collections.abc import Collection, Mapping
from dataclasses import replace

from test_service.domain.ports.output.runners.runner_dtos import (
    RunnerActionOutcome,
    RunnerTestCaseOutcome,
)

REDACTED = "[REDACTED]"


def redact_test_case_outcome(
    outcome: RunnerTestCaseOutcome, secrets: Collection[str]
) -> RunnerTestCaseOutcome:
    """Return the outcome with resolved secrets removed from every free-form field.

    Args:
        outcome: Outcome reported by a runner.
        secrets: Resolved secret values to remove. Empty values are ignored. Longer values
            are replaced first so a secret containing another is removed entirely.

    Returns:
        The same outcome when there is nothing to remove, otherwise a copy where each
        secret in text, mappings and sequences is replaced by a fixed marker.
    """
    ordered = sorted((secret for secret in secrets if secret), key=len, reverse=True)
    if not ordered:
        return outcome
    return replace(
        outcome,
        actions=tuple(_redact_action(action, ordered) for action in outcome.actions),
        error_message=_redact(outcome.error_message, ordered),
    )


def _redact_action(action: RunnerActionOutcome, secrets: list[str]) -> RunnerActionOutcome:
    return replace(
        action,
        expected=_redact(action.expected, secrets),
        actual=_redact(action.actual, secrets),
        output=_redact(action.output, secrets),
        error_message=_redact(action.error_message, secrets),
    )


def _redact(value, secrets: list[str]):
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, REDACTED)
        return value
    if isinstance(value, Mapping):
        return {_redact(key, secrets): _redact(item, secrets) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_redact(item, secrets) for item in value]
    return value
