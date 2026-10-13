"""Project Catalog aggregate."""

import re
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from test_service.domain.model.exceptions.invalid_project_deletion_exception import (
    InvalidProjectDeletionException,
)
from test_service.domain.model.exceptions.invalid_project_key_exception import (
    InvalidProjectKeyException,
)
from test_service.domain.model.exceptions.project_already_deleted_exception import (
    ProjectAlreadyDeletedException,
)

# Jira project key shape, bounded by the 20 characters the API contract allows.
_PROJECT_KEY = re.compile(r"[A-Z][A-Z0-9_]{1,19}")


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
        InvalidProjectKeyException: If the key does not follow the accepted key format.
        InvalidProjectDeletionException:
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
            InvalidProjectKeyException: If the key does not follow the accepted key format.
            InvalidProjectDeletionException: If deletion metadata is inconsistent with the
            lifecycle.
        """
        if not isinstance(self.key, str) or _PROJECT_KEY.fullmatch(self.key) is None:
            raise InvalidProjectKeyException(
                "project key must start with an uppercase letter and contain only uppercase "
                "letters, digits or underscores (2 to 20 characters)"
            )
        self._validate_deletion_metadata()

    def delete(self, deleted_at: datetime, deleted_by: str) -> "Project":
        """Return the logically deleted project.

        Args:
            deleted_at: Timestamp of the logical deletion.
            deleted_by: Identity requesting the logical deletion.

        Returns:
            A new project instance in the ``DELETED`` state.

        Raises:
            ProjectAlreadyDeletedException:
                If the project is already deleted or deletion data is invalid.
        """
        if self.status is ProjectStatus.DELETED:
            raise ProjectAlreadyDeletedException("project is already deleted")
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
            raise InvalidProjectDeletionException("deleted projects require deletion metadata")
        if self.status is ProjectStatus.ACTIVE and (
            has_deletion_timestamp or has_deletion_identity
        ):
            raise InvalidProjectDeletionException("active projects cannot have deletion metadata")
