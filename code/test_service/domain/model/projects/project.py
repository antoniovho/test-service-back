"""Project Catalog aggregate."""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from test_service.domain.model.exceptions.domain_exception import BusinessRuleViolationException


class ProjectStatus(StrEnum):
    """Lifecycle state of a Project Catalog entry.

    Attributes:
        ACTIVE: The project accepts new test resources.
        DELETED: The project is logically deleted while preserving its history.
    """

    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


@dataclass(frozen=True, slots=True)
class Project:
    """Project Catalog entry that scopes Test Service resources.

    Args:
        key: Stable key used to identify the project.
        name: Human-readable project name.
        created_at: Timestamp when the project was registered.
        created_by: Identity that registered the project.
        status: Current lifecycle state.
        deleted_at: Timestamp of logical deletion, when applicable.
        deleted_by: Identity that logically deleted the project, when applicable.

    Raises:
        BusinessRuleViolationException:
        If fields are invalid or deletion metadata is inconsistent.
    """

    key: str
    name: str
    created_at: datetime
    created_by: str
    status: ProjectStatus = ProjectStatus.ACTIVE
    deleted_at: datetime | None = None
    deleted_by: str | None = None

    def __post_init__(self) -> None:
        """Validate Project Catalog invariants.

        Raises:
            BusinessRuleViolationException: If deletion metadata is inconsistent with the lifecycle.
        """
        self._validate_deletion_metadata()

    def delete(self, deleted_at: datetime, deleted_by: str) -> "Project":
        """Return the logically deleted project.

        Args:
            deleted_at: Timestamp of the logical deletion.
            deleted_by: Identity requesting the logical deletion.

        Returns:
            A new project instance in the ``DELETED`` state.

        Raises:
            BusinessRuleViolationException:
                If the project is already deleted or deletion data is invalid.
        """
        if self.status is ProjectStatus.DELETED:
            raise BusinessRuleViolationException(
                "project is already deleted",
                "PROJECT_ALREADY_DELETED",
            )
        return replace(
            self,
            status=ProjectStatus.DELETED,
            deleted_at=deleted_at,
            deleted_by=deleted_by,
        )

    def _validate_deletion_metadata(self) -> None:
        has_deletion_timestamp = self.deleted_at is not None
        has_deletion_identity = self.deleted_by is not None
        if self.status is ProjectStatus.DELETED and not (
            has_deletion_timestamp and has_deletion_identity
        ):
            raise BusinessRuleViolationException(
                "deleted projects require deletion metadata",
                "INVALID_PROJECT_DELETION",
            )
        if self.status is ProjectStatus.ACTIVE and (
            has_deletion_timestamp or has_deletion_identity
        ):
            raise BusinessRuleViolationException(
                "active projects cannot have deletion metadata",
                "INVALID_PROJECT_DELETION",
            )
