"""Environment domain persistence adapter."""

from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.execution.environment import Environment
from test_service.domain.ports.output.persistence.environments.environment_persistence_port import (  # noqa: E501
    EnvironmentPersistencePort,
)
from test_service.infrastructure.adapters.output.execution.environments.persistence.mappers.environment_persistence_mapper import (  # noqa: E501
    EnvironmentPersistenceMapper,
)
from test_service.infrastructure.adapters.output.execution.environments.persistence.repositories.environment_repository import (  # noqa: E501
    EnvironmentRepository,
)


class EnvironmentPersistenceAdapter(EnvironmentPersistencePort):
    """Adapt Environment aggregates to persistence DTO operations."""

    def __init__(self, repository: EnvironmentRepository) -> None:
        self._repository = repository

    async def save(self, environment: Environment) -> Environment:
        return EnvironmentPersistenceMapper.to_domain(
            await self._repository.save(EnvironmentPersistenceMapper.to_dto(environment))
        )

    async def find_by_id(self, identifier: UUID) -> Environment | None:
        environment = await self._repository.find_by_id(identifier)
        return (
            EnvironmentPersistenceMapper.to_domain(environment) if environment is not None else None
        )

    async def find_by_key(self, environment_key: str) -> Environment | None:
        environment = await self._repository.find_by_key(environment_key)
        return (
            EnvironmentPersistenceMapper.to_domain(environment) if environment is not None else None
        )

    async def find_page(self, pagination: PaginationParams) -> Page[Environment]:
        page = await self._repository.find_page(pagination)
        return Page(
            items=tuple(
                EnvironmentPersistenceMapper.to_domain(environment) for environment in page.items
            ),
            total=page.total,
        )
