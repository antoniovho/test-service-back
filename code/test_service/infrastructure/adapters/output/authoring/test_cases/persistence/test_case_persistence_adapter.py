"""Test Case domain persistence adapter."""

from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)
from test_service.infrastructure.adapters.output.authoring.test_cases.persistence.mappers.test_case_persistence_mapper import (  # noqa: E501
    TestCasePersistenceMapper,
)
from test_service.infrastructure.adapters.output.authoring.test_cases.persistence.repositories.test_case_repository import (  # noqa: E501
    TestCaseRepository,
)


class TestCasePersistenceAdapter(TestCasePersistencePort):
    """Adapt Test Case aggregates to persistence DTO operations."""

    def __init__(self, repository: TestCaseRepository) -> None:
        self._repository = repository

    async def save(self, snapshot: TestCase) -> TestCase:
        return TestCasePersistenceMapper.to_domain(
            await self._repository.save(TestCasePersistenceMapper.to_dto(snapshot))
        )

    async def find_by_id(self, identifier: UUID) -> TestCase | None:
        snapshot = await self._repository.find_by_id(identifier)
        return TestCasePersistenceMapper.to_domain(snapshot) if snapshot is not None else None

    async def find_latest_version(self, project_key: str, test_key: str) -> int | None:
        return await self._repository.find_latest_version(project_key, test_key)

    async def find_page(
        self, project_key: str, pagination: PaginationParams, status: VersionStatus | None = None
    ) -> Page[TestCase]:
        return await self._to_domain_page(
            await self._repository.find_page(project_key, pagination, status)
        )

    async def find_versions(
        self,
        project_key: str,
        test_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestCase]:
        return await self._to_domain_page(
            await self._repository.find_versions(project_key, test_key, pagination, status)
        )

    @staticmethod
    async def _to_domain_page(page: Page) -> Page[TestCase]:
        return Page(
            items=tuple(TestCasePersistenceMapper.to_domain(snapshot) for snapshot in page.items),
            total=page.total,
        )
