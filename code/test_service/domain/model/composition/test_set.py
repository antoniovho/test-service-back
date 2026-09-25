"""Immutable TestSet snapshot aggregate."""

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from test_service.domain.model.exceptions.domain_exception import BusinessRuleViolationException
from test_service.domain.model.lifecycle import VersionStatus, activate_status, deprecate_status


@dataclass(frozen=True, slots=True)
class TestSet:
    """Immutable ordered collection of exact test case snapshots.

    Args:
        identifier: UUID of this immutable snapshot.
        project_key: Owning project key.
        set_key: Stable logical test set key.
        version: Positive version number of this snapshot.
        name: Human-readable name.
        items: Ordered UUIDs of test case snapshots.
        created_at: Creation timestamp.
        created_by: Identity that created the snapshot.
        description: Optional purpose of the set.
        status: Snapshot lifecycle state.

    Raises:
        BusinessRuleViolationException: If the version or item collection is invalid.
    """

    identifier: UUID
    project_key: str
    set_key: str
    version: int
    name: str
    items: tuple[UUID, ...]
    created_at: datetime
    created_by: str
    description: str | None = None
    status: VersionStatus = VersionStatus.DRAFT

    def __post_init__(self) -> None:
        """Validate TestSet snapshot invariants.

        Raises:
            BusinessRuleViolationException:
                If the version is invalid or items are empty or duplicated.
        """
        if self.version < 1:
            raise BusinessRuleViolationException("version must be positive", "INVALID_TEST_SET")
        if not self.items or len(set(self.items)) != len(self.items):
            raise BusinessRuleViolationException(
                "test set items must be non-empty and unique",
                "INVALID_TEST_SET",
            )

    def activate(self) -> "TestSet":
        """Return this snapshot in the active state.

        Returns:
            A new active test set snapshot.

        Raises:
            BusinessRuleViolationException: If this snapshot is not a draft.
        """
        return replace(self, status=activate_status(self.status))

    def deprecate(self) -> "TestSet":
        """Return this snapshot in the deprecated state.

        Returns:
            A new deprecated test set snapshot.

        Raises:
            BusinessRuleViolationException: If this snapshot is not active.
        """
        return replace(self, status=deprecate_status(self.status))
