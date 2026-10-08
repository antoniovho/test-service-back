"""Immutable TestPlan snapshot aggregate."""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from test_service.domain.model.exceptions.invalid_test_plan_exception import (
    InvalidTestPlanException,
)
from test_service.domain.model.lifecycle import VersionStatus, activate_status, deprecate_status


class ExecutionMode(StrEnum):
    """Scheduling mode for a TestPlan.

    Attributes:
        SEQUENTIAL: Executes plan items one by one.
    """

    SEQUENTIAL = "SEQUENTIAL"


@dataclass(frozen=True, slots=True)
class TestPlan:
    """Immutable executable plan composed from exact snapshots.

    Args:
        identifier: UUID of this immutable snapshot.
        project_key: Owning project key.
        plan_key: Stable logical test plan key.
        version: Positive version number of this snapshot.
        name: Human-readable name.
        execution_mode: Scheduling mode for plan items.
        timeout_seconds: Maximum plan execution time.
        created_at: Creation timestamp.
        created_by: Identity that created the snapshot.
        test_set_ids: Ordered test set snapshot UUIDs.
        test_case_ids: Ordered individual test case snapshot UUIDs.
        exclusions: Test case snapshot UUIDs excluded from the plan.
        description: Optional plan purpose.
        status: Snapshot lifecycle state.

    Raises:
        InvalidTestPlanException: If snapshot content violates plan invariants.
    """

    identifier: UUID
    project_key: str
    plan_key: str
    version: int
    name: str
    execution_mode: ExecutionMode
    timeout_seconds: int
    created_at: datetime
    created_by: str
    test_set_ids: tuple[UUID, ...] = ()
    test_case_ids: tuple[UUID, ...] = ()
    exclusions: tuple[UUID, ...] = ()
    description: str | None = None
    status: VersionStatus = VersionStatus.DRAFT

    def __post_init__(self) -> None:
        """Validate TestPlan snapshot invariants.

        Raises:
            InvalidTestPlanException: If the version, timeout, references, or mode is invalid.
        """
        if self.version < 1 or self.timeout_seconds < 1:
            raise InvalidTestPlanException("version and timeout must be positive")
        self._validate_unique_references()

    def activate(self) -> "TestPlan":
        """Return this snapshot in the active state.

        Returns:
            A new active test plan snapshot.

        Raises:
            InvalidLifecycleTransitionException: If this snapshot is not a draft.
        """
        return replace(self, status=activate_status(self.status))

    def deprecate(self) -> "TestPlan":
        """Return this snapshot in the deprecated state.

        Returns:
            A new deprecated test plan snapshot.

        Raises:
            InvalidLifecycleTransitionException: If this snapshot is not active.
        """
        return replace(self, status=deprecate_status(self.status))

    def _validate_unique_references(self) -> None:
        collections = (self.test_set_ids, self.test_case_ids, self.exclusions)
        if any(len(set(item_ids)) != len(item_ids) for item_ids in collections):
            raise InvalidTestPlanException(
                "test plan references must be unique within each collection"
            )
        if set(self.test_case_ids).intersection(self.exclusions):
            raise InvalidTestPlanException("test plan cannot exclude a directly included test case")
