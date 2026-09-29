"""Test Set domain persistence adapter."""

from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)
from test_service.infrastructure.adapters.output.composition.test_sets.persistence.mappers.test_set_persistence_mapper import (  # noqa: E501
    TestSetPersistenceMapper,
)
from test_service.infrastructure.adapters.output.composition.test_sets.persistence.repositories.test_set_repository import (  # noqa: E501
    TestSetRepository,
)


class TestSetPersistenceAdapter(TestSetPersistencePort):
    """Adapt Test Set aggregates to persistence DTO operations."""

    def __init__(self, repository: TestSetRepository) -> None:
        self._repository = repository

    async def save(self, snapshot: TestSet) -> TestSet:
        return TestSetPersistenceMapper.to_domain(
            await self._repository.save(TestSetPersistenceMapper.to_dto(snapshot))
        )

    async def find_by_id(self, identifier: UUID) -> TestSet | None:
        snapshot = await self._repository.find_by_id(identifier)
        return TestSetPersistenceMapper.to_domain(snapshot) if snapshot is not None else None

    async def find_latest_version(self, project_key: str, set_key: str) -> int | None:
        return await self._repository.find_latest_version(project_key, set_key)

    async def find_page(
        self, project_key: str, pagination: PaginationParams, status: VersionStatus | None = None
    ) -> Page[TestSet]:
        return self._to_domain_page(
            await self._repository.find_page(project_key, pagination, status)
        )

    async def find_versions(
        self,
        project_key: str,
        set_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestSet]:
        return self._to_domain_page(
            await self._repository.find_versions(project_key, set_key, pagination, status)
        )

    @staticmethod
    def _to_domain_page(page: Page) -> Page[TestSet]:
        return Page(
            items=tuple(TestSetPersistenceMapper.to_domain(snapshot) for snapshot in page.items),
            total=page.total,
        )
