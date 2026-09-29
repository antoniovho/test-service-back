"""Commands for Project Catalog use cases."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CreateProjectCommand:
    """Request to register a validated project.

    Args:
        key: Stable project key.
        name: Human-readable project name.
        requested_by: Identity requesting registration.
        requested_at: Registration timestamp.
    """

    key: str
    name: str
    requested_by: str
    requested_at: datetime


@dataclass(frozen=True, slots=True)
class DeleteProjectCommand:
    """Request to logically delete one project.

    Args:
        key: Stable project key.
        requested_by: Identity requesting deletion.
        requested_at: Deletion timestamp.
    """

    key: str
    requested_by: str
    requested_at: datetime
