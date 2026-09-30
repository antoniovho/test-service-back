"""Execution domain persistence adapter."""

from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.execution.execution import Execution
from test_service.domain.ports.output.persistence.executions.execution_persistence_port import (  # noqa: E501
    ExecutionPersistencePort,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.mappers.execution_persistence_mapper import (  # noqa: E501
    ExecutionPersistenceMapper,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.repositories.execution_repository import (  # noqa: E501
    ExecutionRepository,
)


class ExecutionPersistenceAdapter(ExecutionPersistencePort):
    """Adapt Execution aggregates to persistence DTO operations."""

    def __init__(self, repository: ExecutionRepository) -> None:
        self._repository = repository

    async def save_execution(self, execution: Execution) -> Execution:
        return ExecutionPersistenceMapper.to_domain(
            await self._repository.save(ExecutionPersistenceMapper.to_dto(execution))
        )

    async def find_execution(self, identifier: UUID) -> Execution | None:
        execution = await self._repository.find_by_id(identifier)
        return ExecutionPersistenceMapper.to_domain(execution) if execution is not None else None

    async def find_page(self, project_key: str, pagination: PaginationParams) -> Page[Execution]:
        page = await self._repository.find_page(project_key, pagination)
        return Page(
            items=tuple(
                ExecutionPersistenceMapper.to_domain(execution) for execution in page.items
            ),
            total=page.total,
        )
