"""Execution and immutable execution-result models."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from test_service.domain.commons.immutable import freeze_mapping
from test_service.domain.model.exceptions.invalid_artifact_storage_exception import (
    InvalidArtifactStorageException,
)
from test_service.domain.model.exceptions.invalid_execution_transition_exception import (
    InvalidExecutionTransitionException,
)
from test_service.domain.model.exceptions.invalid_temporal_data_exception import (
    InvalidTemporalDataException,
)


class TriggerType(StrEnum):
    """Source that initiated an execution.

    Attributes:
        MANUAL: A person initiated the execution.
        API: An API client initiated the execution.
        CI: A continuous integration system initiated the execution.
        SCHEDULE: A scheduler initiated the execution.
    """

    MANUAL = "MANUAL"
    API = "API"
    CI = "CI"
    SCHEDULE = "SCHEDULE"


class ExecutionStatus(StrEnum):
    """Lifecycle state of an execution.

    Attributes:
        CREATED: Execution has been accepted but not started.
        RUNNING: Execution is being processed.
        PASSED: Execution completed successfully.
        FAILED: Execution completed with failures.
        PARTIALLY_FAILED: Execution completed with mixed outcomes.
        CANCELLED: Execution was cancelled before completion.
        ERROR: Execution could not complete due to an error.
    """

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    PARTIALLY_FAILED = "PARTIALLY_FAILED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


_RUNNER_TERMINAL_STATUSES = frozenset(
    {
        ExecutionStatus.PASSED,
        ExecutionStatus.FAILED,
        ExecutionStatus.PARTIALLY_FAILED,
        ExecutionStatus.ERROR,
    }
)

TERMINAL_EXECUTION_STATUSES = _RUNNER_TERMINAL_STATUSES | frozenset({ExecutionStatus.CANCELLED})


class ResultStatus(StrEnum):
    """Outcome state of a test or action result.

    Attributes:
        PASSED: The result met its expected outcome.
        FAILED: The result did not meet its expected outcome.
        ERROR: The result could not be evaluated.
        BLOCKED: The result could not start due to a prerequisite.
        SKIPPED: The result was intentionally not run.
    """

    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class ArtifactType(StrEnum):
    """Classification of technical evidence.

    Attributes:
        REQUEST: Request evidence.
        RESPONSE: Response evidence.
        SSE_TRACE: Server-sent event trace evidence.
        LOG: Log evidence.
        OTHER: Other technical evidence.
    """

    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    SSE_TRACE = "SSE_TRACE"
    LOG = "LOG"
    OTHER = "OTHER"


class StorageType(StrEnum):
    """Persistence location for an artifact payload.

    Attributes:
        DB: Artifact is stored by the database adapter.
        OBJECT_STORAGE: Artifact is stored by an object-store adapter.
    """

    DB = "DB"
    OBJECT_STORAGE = "OBJECT_STORAGE"


@dataclass(frozen=True, slots=True)
class Execution:
    """One execution of exact plan and environment snapshots.

    Args:
        identifier: UUID of the execution.
        project_key: Owning project key.
        test_plan_id: UUID of the executed test plan snapshot.
        environment_id: UUID of the environment used for execution.
        test_case_ids: Ordered Test Case snapshot UUIDs selected at scheduling.
        environment_snapshot: Safe unresolved environment configuration at scheduling.
        trigger_type: Source of the execution request.
        created_at: Request acceptance timestamp.
        status: Current execution lifecycle state.
        triggered_by: Optional initiating identity.
        runner_identifier: Optional stable identifier of the accepted runner.
        runner_version: Optional runner version.
        started_at: Optional start timestamp.
        finished_at: Optional completion timestamp.
        duration_ms: Optional measured duration.

    Raises:
        InvalidTemporalDataException: If timestamps or duration are inconsistent.
    """

    identifier: UUID
    project_key: str
    test_plan_id: UUID
    environment_id: UUID
    trigger_type: TriggerType
    created_at: datetime
    test_case_ids: tuple[UUID, ...] = ()
    environment_snapshot: Mapping[str, object] | None = None
    status: ExecutionStatus = ExecutionStatus.CREATED
    triggered_by: str | None = None
    runner_identifier: str | None = None
    runner_version: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None

    def __post_init__(self) -> None:
        """Validate temporal execution data.

        Raises:
            InvalidTemporalDataException: If timestamps or duration are inconsistent.
        """
        _validate_temporal_data(self.started_at, self.finished_at, self.duration_ms)
        object.__setattr__(self, "environment_snapshot", freeze_mapping(self.environment_snapshot))

    def start(self, started_at: datetime) -> "Execution":
        """Return this execution transitioned from CREATED to RUNNING.

        Args:
            started_at: Timestamp when the runner began processing the execution.

        Returns:
            A new running execution with ``started_at`` set.

        Raises:
            InvalidExecutionTransitionException: If the execution is not in the CREATED state.
        """
        if self.status is not ExecutionStatus.CREATED:
            raise InvalidExecutionTransitionException("only created executions can start running")
        return replace(self, status=ExecutionStatus.RUNNING, started_at=started_at)

    def complete(self, status: ExecutionStatus, finished_at: datetime) -> "Execution":
        """Return this execution transitioned from RUNNING to a terminal outcome.

        Args:
            status: Terminal outcome reached by the runner.
            finished_at: Timestamp when the runner finished processing the execution.

        Returns:
            A new terminal execution with ``finished_at`` and ``duration_ms`` set.

        Raises:
            InvalidExecutionTransitionException:
                If the execution is not RUNNING or the target status is not a runner outcome.
        """
        if self.status is not ExecutionStatus.RUNNING:
            raise InvalidExecutionTransitionException("only running executions can complete")
        if status not in _RUNNER_TERMINAL_STATUSES:
            raise InvalidExecutionTransitionException(
                "completion status must be a runner-reported terminal outcome"
            )
        return replace(
            self,
            status=status,
            finished_at=finished_at,
            duration_ms=_elapsed_ms(self.started_at, finished_at),
        )

    def cancel(self, finished_at: datetime | None = None) -> "Execution":
        """Return a cancelled execution when it has not reached a terminal state.

        Args:
            finished_at: Optional timestamp when the cancellation took effect. Required to
                measure ``duration_ms`` when the execution had already started running.

        Returns:
            A new cancelled execution.

        Raises:
            InvalidExecutionTransitionException: If the execution is already terminal.
        """
        if self.status in TERMINAL_EXECUTION_STATUSES:
            raise InvalidExecutionTransitionException("terminal executions cannot be cancelled")
        duration_ms = _elapsed_ms(self.started_at, finished_at) if finished_at else None
        return replace(
            self,
            status=ExecutionStatus.CANCELLED,
            finished_at=finished_at if finished_at else self.finished_at,
            duration_ms=duration_ms,
        )


@dataclass(frozen=True, slots=True)
class TestResult:
    """Immutable aggregate outcome for one executed test case.

    Args:
        identifier: UUID of the result.
        execution_id: UUID of the owning execution.
        test_case_id: UUID of the executed test case snapshot.
        status: Outcome state.
        created_at: Result creation timestamp.
        started_at: Optional start timestamp.
        finished_at: Optional completion timestamp.
        duration_ms: Optional measured duration.
        error_code: Optional machine-readable failure code.
        error_message: Optional safe failure explanation.
    """

    identifier: UUID
    execution_id: UUID
    test_case_id: UUID
    status: ResultStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        """Validate temporal result data.

        Raises:
            InvalidTemporalDataException: If timestamps or duration are inconsistent.
        """
        _validate_temporal_data(self.started_at, self.finished_at, self.duration_ms)


@dataclass(frozen=True, slots=True)
class ActionResult:
    """Immutable outcome for an action in a test result.

    Args:
        identifier: UUID of the action result.
        test_result_id: UUID of the owning test result.
        action_id: Definition-local action identifier.
        action_type: Resolved action type.
        status: Outcome state.
        created_at: Action-result creation timestamp.
        expected: Optional expected small structured value.
        actual: Optional actual small structured value.
        output: Optional action-produced small structured value.
        started_at: Optional start timestamp.
        finished_at: Optional completion timestamp.
        duration_ms: Optional measured duration.
        error_code: Optional machine-readable failure code.
        error_message: Optional safe failure explanation.
    """

    identifier: UUID
    test_result_id: UUID
    action_id: str
    action_type: str
    status: ResultStatus
    created_at: datetime
    expected: Mapping[str, object] | None = None
    actual: Mapping[str, object] | None = None
    output: Mapping[str, object] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        """Validate temporal action-result data and freeze mutable structured fields.

        Raises:
            InvalidTemporalDataException: If timestamps or duration are inconsistent.
        """
        _validate_temporal_data(self.started_at, self.finished_at, self.duration_ms)
        object.__setattr__(self, "expected", freeze_mapping(self.expected))
        object.__setattr__(self, "actual", freeze_mapping(self.actual))
        object.__setattr__(self, "output", freeze_mapping(self.output))


@dataclass(frozen=True, slots=True)
class TestResultArtifact:
    """Metadata reference for potentially large execution evidence.

    Args:
        identifier: UUID of the artifact.
        test_result_id: UUID of the owning test result.
        artifact_type: Evidence classification.
        storage_type: Adapter responsible for payload storage.
        created_at: Artifact creation timestamp.
        action_result_id: Optional associated action result UUID.
        storage_uri: Optional object storage retrieval URI.
        content_hash: Optional integrity hash.
        size_bytes: Optional payload size.
        mime_type: Optional media type.
    """

    identifier: UUID
    test_result_id: UUID
    artifact_type: ArtifactType
    storage_type: StorageType
    created_at: datetime
    action_result_id: UUID | None = None
    storage_uri: str | None = None
    content_hash: str | None = None
    size_bytes: int | None = None
    mime_type: str | None = None

    def __post_init__(self) -> None:
        """Validate artifact storage metadata.

        Raises:
            InvalidArtifactStorageException: If storage metadata conflicts with the backend.
        """
        if self.size_bytes is not None and self.size_bytes < 0:
            raise InvalidArtifactStorageException("artifact size must not be negative")
        if self.storage_type is StorageType.DB and self.storage_uri is not None:
            raise InvalidArtifactStorageException("database artifacts cannot define a storage URI")
        if self.storage_type is StorageType.OBJECT_STORAGE and self.storage_uri is None:
            raise InvalidArtifactStorageException("object storage artifacts require a storage URI")


def _validate_temporal_data(
    started_at: datetime | None,
    finished_at: datetime | None,
    duration_ms: int | None,
) -> None:
    """Validate optional execution timestamps and duration.

    Args:
        started_at: Optional operation start timestamp.
        finished_at: Optional operation completion timestamp.
        duration_ms: Optional measured operation duration.

    Raises:
        InvalidTemporalDataException: If duration is negative or completion precedes start.
    """
    if duration_ms is not None and duration_ms < 0:
        raise InvalidTemporalDataException("duration must not be negative")
    if started_at is not None and finished_at is not None and finished_at < started_at:
        raise InvalidTemporalDataException("operation cannot finish before it starts")


def _elapsed_ms(started_at: datetime | None, finished_at: datetime) -> int | None:
    """Compute the elapsed milliseconds between an optional start and a completion timestamp.

    Args:
        started_at: Optional operation start timestamp.
        finished_at: Operation completion timestamp.

    Returns:
        Elapsed milliseconds, or ``None`` when ``started_at`` is unknown.

    Raises:
        InvalidTemporalDataException: If completion precedes the start timestamp.
    """
    if started_at is None:
        return None
    if finished_at < started_at:
        raise InvalidTemporalDataException("operation cannot finish before it starts")
    return int((finished_at - started_at).total_seconds() * 1000)
