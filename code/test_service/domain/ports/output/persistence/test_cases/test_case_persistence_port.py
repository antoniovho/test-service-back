"""Test Case persistence contract."""

from typing import Protocol

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.versioned.versioned_persistence_port import (
    VersionedPersistencePort,
)


class TestCasePersistencePort(VersionedPersistencePort[TestCase], Protocol):
    """Persistence contract for Test Case snapshots."""

    async def find_latest_version(self, project_key: str, test_key: str) -> int | None:
        """Find the highest-numbered version for one logical Test Case."""
        ...

    async def find_page(
        self,
        project_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestCase]:
        """Find Test Case snapshots owned by one project."""
        ...

    async def find_versions(
        self,
        project_key: str,
        test_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestCase]:
        """Find every Test Case snapshot sharing one project-scoped key."""
        ...
