"""Technical DTOs exchanged by the Tavern subprocess integration."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TavernStageResult:
    """Machine-readable data emitted for a single Tavern stage."""

    identifier: str
    status: str
    started_at: datetime
    finished_at: datetime
    expected: Mapping[str, object] | None = None
    actual: Mapping[str, object] | None = None
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class TavernExecutionResult:
    """Technical result returned by one isolated Tavern subprocess."""

    exit_code: int
    cancelled: bool
    stages: tuple[TavernStageResult, ...]
    variables: Mapping[str, str]
