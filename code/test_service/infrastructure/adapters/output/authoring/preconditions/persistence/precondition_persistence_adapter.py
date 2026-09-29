"""Precondition persistence adapter used to resolve Test Case references."""

from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.mappers.precondition_persistence_mapper import (  # noqa: E501
    PreconditionPersistenceMapper,
)
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.repositories.precondition_repository import (  # noqa: E501
    PreconditionRepository,
)


class PreconditionPersistenceAdapter(PreconditionPersistencePort):
    """Adapt lookup DTO operations to the Precondition domain port."""

    def __init__(self, repository: PreconditionRepository) -> None:
        self._repository = repository

    async def find_by_id(self, identifier: UUID) -> Precondition | None:
        precondition = await self._repository.find_by_id(identifier)
        return (
            PreconditionPersistenceMapper.to_domain(precondition)
            if precondition is not None
            else None
        )

    async def save(self, snapshot: Precondition) -> Precondition:
        return PreconditionPersistenceMapper.to_domain(
            await self._repository.save(PreconditionPersistenceMapper.to_dto(snapshot))
        )

    async def find_latest_version(self, project_key: str, precondition_key: str) -> int | None:
        return await self._repository.find_latest_version(project_key, precondition_key)

    async def find_page(
        self, project_key: str, pagination: PaginationParams, status: VersionStatus | None = None
    ) -> Page[Precondition]:
        return await self._to_domain_page(
            await self._repository.find_page(project_key, pagination, status)
        )

    async def find_versions(
        self,
        project_key: str,
        precondition_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[Precondition]:
        return await self._to_domain_page(
            await self._repository.find_versions(project_key, precondition_key, pagination, status)
        )

    @staticmethod
    async def _to_domain_page(page: Page) -> Page[Precondition]:
        return Page(
            items=tuple(
                PreconditionPersistenceMapper.to_domain(snapshot) for snapshot in page.items
            ),
            total=page.total,
        )
