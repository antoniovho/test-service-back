"""Precondition persistence contract."""

from typing import Protocol

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.versioned.versioned_persistence_port import (
    VersionedPersistencePort,
)


class PreconditionPersistencePort(VersionedPersistencePort[Precondition], Protocol):
    """Persistence contract for Precondition snapshots."""

    async def find_page(
        self,
        project_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[Precondition]:
        """Find Precondition snapshots owned by one project."""
        ...

    async def find_versions(
        self,
        project_key: str,
        precondition_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[Precondition]:
        """Find every Precondition snapshot sharing one project-scoped key."""
        ...
