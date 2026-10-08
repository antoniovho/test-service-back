"""External validation contract for a Project key."""

from typing import Protocol


class ProjectValidationPort(Protocol):
    """Validate a Project against the configured external system of record."""

    async def validate(self, project_key: str) -> None:
        """Return only when the external project exists and is accessible."""
        ...
