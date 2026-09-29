"""Test Plan domain persistence adapter."""

from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (
    TestPlanPersistencePort,
)
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.mappers.test_plan_persistence_mapper import (  # noqa: E501
    TestPlanPersistenceMapper,
)
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.repositories.test_plan_repository import (  # noqa: E501
    TestPlanRepository,
)


class TestPlanPersistenceAdapter(TestPlanPersistencePort):
    """Adapt Test Plan aggregates to persistence DTO operations."""

    def __init__(self, repository: TestPlanRepository) -> None:
        self._repository = repository

    async def save(self, snapshot: TestPlan) -> TestPlan:
        """Persist one Test Plan snapshot."""
        return TestPlanPersistenceMapper.to_domain(
            await self._repository.save(TestPlanPersistenceMapper.to_dto(snapshot))
        )

    async def find_by_id(self, identifier: UUID) -> TestPlan | None:
        """Find one Test Plan snapshot by UUID."""
        snapshot = await self._repository.find_by_id(identifier)
        return TestPlanPersistenceMapper.to_domain(snapshot) if snapshot is not None else None

    async def find_latest_version(self, project_key: str, plan_key: str) -> int | None:
        """Find the newest version for one logical Test Plan."""
        return await self._repository.find_latest_version(project_key, plan_key)

    async def find_page(
        self, project_key: str, pagination: PaginationParams, status: VersionStatus | None = None
    ) -> Page[TestPlan]:
        """Find a project-scoped Test Plan page."""
        return self._to_domain_page(
            await self._repository.find_page(project_key, pagination, status)
        )

    async def find_versions(
        self,
        project_key: str,
        plan_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestPlan]:
        """Find Test Plan versions sharing one key."""
        return self._to_domain_page(
            await self._repository.find_versions(project_key, plan_key, pagination, status)
        )

    @staticmethod
    def _to_domain_page(page: Page) -> Page[TestPlan]:
        return Page(
            items=tuple(TestPlanPersistenceMapper.to_domain(snapshot) for snapshot in page.items),
            total=page.total,
        )
