"""Shared persistence contract for immutable versioned snapshots."""

from typing import Protocol
from uuid import UUID


class VersionedPersistencePort[Snapshot](Protocol):
    """Persistence contract for immutable versioned snapshots."""

    async def save(self, snapshot: Snapshot) -> Snapshot:
        """Persist a new or transitioned snapshot."""
        ...

    async def find_by_id(self, identifier: UUID) -> Snapshot | None:
        """Find a snapshot by UUID."""
        ...
