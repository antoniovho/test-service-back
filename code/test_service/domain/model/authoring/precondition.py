"""Immutable Precondition snapshot aggregate."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from test_service.domain.commons.immutable import freeze_mapping
from test_service.domain.model.authoring.definition import Definition
from test_service.domain.model.exceptions.domain_exception import BusinessRuleViolationException
from test_service.domain.model.lifecycle import VersionStatus, activate_status, deprecate_status


@dataclass(frozen=True, slots=True)
class Precondition:
    """Immutable validation prerequisite snapshot.

    Args:
        identifier: UUID of this immutable snapshot.
        project_key: Owning project key.
        precondition_key: Stable logical precondition key.
        version: Positive version number of this snapshot.
        name: Human-readable name.
        description: Purpose of the prerequisite.
        validation_definition: Definition used to validate the prerequisite.
        created_at: Creation timestamp.
        created_by: Identity that created the snapshot.
        status: Snapshot lifecycle state.
        metadata: Additional safe domain metadata.

    Raises:
        BusinessRuleViolationException: If the version is not positive.
    """

    identifier: UUID
    project_key: str
    precondition_key: str
    version: int
    name: str
    description: str
    validation_definition: Definition
    created_at: datetime
    created_by: str
    status: VersionStatus = VersionStatus.DRAFT
    metadata: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        """Validate immutable Precondition invariants and freeze mutable metadata.

        Raises:
            BusinessRuleViolationException: If the version is not positive.
        """
        if self.version < 1:
            raise BusinessRuleViolationException("version must be positive", "INVALID_PRECONDITION")
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))

    def activate(self) -> "Precondition":
        """Return this snapshot in the active state.

        Returns:
            A new active precondition snapshot.

        Raises:
            BusinessRuleViolationException: If this snapshot is not a draft.
        """
        return replace(self, status=activate_status(self.status))

    def deprecate(self) -> "Precondition":
        """Return this snapshot in the deprecated state.

        Returns:
            A new deprecated precondition snapshot.

        Raises:
            BusinessRuleViolationException: If this snapshot is not active.
        """
        return replace(self, status=deprecate_status(self.status))
