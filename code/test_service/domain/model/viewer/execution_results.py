"""Durable models for publishing local execution results to external viewers."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from test_service.domain.model.viewer.records import ViewerType


class ViewerResultPublicationStatus(StrEnum):
    """Lifecycle states for a durable execution-result publication."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    RETRY_WAIT = "RETRY_WAIT"
    SUCCEEDED = "SUCCEEDED"
    FAILED_PERMANENT = "FAILED_PERMANENT"


@dataclass(frozen=True, slots=True)
class ViewerResultPublication:
    """Durable request to publish one completed local execution."""

    identifier: UUID
    project_key: str
    execution_id: UUID
    viewer_type: ViewerType
    status: ViewerResultPublicationStatus
    created_at: datetime
    updated_at: datetime
    attempts: int = 0
    next_attempt_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    external_execution_id: str | None = None
    external_execution_key: str | None = None
    error: str | None = None

    @property
    def correlation_key(self) -> str:
        """Return the stable external correlation key for this execution."""
        return f"test-service-execution-{self.execution_id}"
