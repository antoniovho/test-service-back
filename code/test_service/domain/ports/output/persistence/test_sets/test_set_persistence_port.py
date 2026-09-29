"""Test Set persistence contract."""

from typing import Protocol

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.versioned.versioned_persistence_port import (
    VersionedPersistencePort,
)


class TestSetPersistencePort(VersionedPersistencePort[TestSet], Protocol):
    """Persistence contract for Test Set snapshots."""

    async def find_latest_version(self, project_key: str, set_key: str) -> int | None:
        """Find the highest-numbered version for one logical Test Set."""
        ...

    async def find_page(
        self,
        project_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestSet]:
        """Find Test Set snapshots owned by one project."""
        ...

    async def find_versions(
        self,
        project_key: str,
        set_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestSet]:
        """Find every Test Set snapshot sharing one project-scoped key."""
        ...
