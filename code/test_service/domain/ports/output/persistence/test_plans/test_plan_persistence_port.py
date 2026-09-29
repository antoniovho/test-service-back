"""Test Plan persistence contract."""

from typing import Protocol

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.versioned.versioned_persistence_port import (
    VersionedPersistencePort,
)


class TestPlanPersistencePort(VersionedPersistencePort[TestPlan], Protocol):
    """Persistence contract for Test Plan snapshots."""

    async def find_latest_version(self, project_key: str, plan_key: str) -> int | None:
        """Find the highest-numbered version for one logical Test Plan."""
        ...

    async def find_page(
        self,
        project_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestPlan]:
        """Find Test Plan snapshots owned by one project."""
        ...

    async def find_versions(
        self,
        project_key: str,
        plan_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestPlan]:
        """Find every Test Plan snapshot sharing one project-scoped key."""
        ...
