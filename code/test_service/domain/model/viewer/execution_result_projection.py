"""Provider-neutral execution-result projection models."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from test_service.domain.model.execution.execution import (
    ExecutionStatus,
    ResultStatus,
)
from test_service.domain.model.viewer.execution_results import ViewerResultPublication


@dataclass(frozen=True, slots=True)
class ViewerEvidenceProjection:
    """One safe inline evidence item ready for an external viewer."""

    filename: str
    mime_type: str
    content: str


@dataclass(frozen=True, slots=True)
class ViewerTestRunProjection:
    """One local TestResult ready to update in the external viewer."""

    test_result_id: UUID
    external_test_id: str
    status: ResultStatus
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    comment: str | None
    evidence: tuple[ViewerEvidenceProjection, ...] = ()


@dataclass(frozen=True, slots=True)
class ViewerExecutionResultProjection:
    """The complete, safe external representation of one local execution."""

    publication: ViewerResultPublication
    summary: str
    environment_name: str
    external_test_plan_id: str
    execution_status: ExecutionStatus
    test_runs: tuple[ViewerTestRunProjection, ...]


@dataclass(frozen=True, slots=True)
class ViewerExecutionResultIdentity:
    """External identities returned after publishing an execution result."""

    execution_id: str
    execution_key: str
    test_run_ids: dict[UUID, str]
