"""Provider-neutral execution work and results exchanged with a Runner."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from test_service.domain.model.execution.execution import ResultStatus


@dataclass(frozen=True, slots=True)
class CompiledAction:
    """A validated action ready for a concrete runner."""

    identifier: str
    action_type: str
    position: int
    configuration: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CompiledTestCase:
    """Runner-independent, immutable executable test case representation."""

    test_case_id: str
    variables: Mapping[str, str]
    actions: tuple[CompiledAction, ...]


@dataclass(frozen=True, slots=True)
class RunnerActionOutcome:
    """Safe normalized result emitted by a runner for one action."""

    action_id: str
    action_type: str
    status: ResultStatus
    started_at: datetime
    finished_at: datetime
    expected: Mapping[str, object] | None = None
    actual: Mapping[str, object] | None = None
    output: Mapping[str, object] | None = None
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class RunnerTestCaseOutcome:
    """Safe canonical outcome for a complete Test Case execution."""

    status: ResultStatus
    started_at: datetime
    finished_at: datetime
    actions: tuple[RunnerActionOutcome, ...]
    error_code: str | None = None
    error_message: str | None = None
