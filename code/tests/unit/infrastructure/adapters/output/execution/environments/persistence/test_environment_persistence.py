from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.execution.environment import Environment, SecretReference
from test_service.infrastructure.adapters.output.execution.environments.environment_persistence_adapter import (  # noqa: E501
    EnvironmentPersistenceAdapter,
)
from test_service.infrastructure.adapters.output.execution.environments.persistence.dtos.environment_dto import (  # noqa: E501
    EnvironmentDTO,
)
from test_service.infrastructure.adapters.output.execution.environments.persistence.mappers.environment_persistence_mapper import (  # noqa: E501
    EnvironmentPersistenceMapper,
)
from test_service.infrastructure.adapters.output.execution.environments.persistence.repositories.environment_repository import (  # noqa: E501
    EnvironmentRepository,
)


def _environment() -> Environment:
    return Environment(
        identifier=uuid4(),
        environment_key="staging-eu",
        name="Staging Europe",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        configuration={"region": "eu-west-1", "api_token": SecretReference("vault", "staging")},
    )


def _dto() -> EnvironmentDTO:
    return EnvironmentPersistenceMapper.to_dto(_environment())


class _Repository:
    def __init__(self, dto: EnvironmentDTO) -> None:
        self.dto = dto
        self.saved: EnvironmentDTO | None = None

    async def save(self, dto: EnvironmentDTO) -> EnvironmentDTO:
        self.saved = dto
        return dto

    async def find_by_id(self, identifier):
        return self.dto

    async def find_by_key(self, environment_key: str):
        return self.dto

    async def find_page(self, pagination):
        return Page((self.dto,), 1)


class _SessionProvider:
    def __init__(self, session: MagicMock) -> None:
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session


class TestEnvironmentPersistence:
    def test_when_mapping_environment_expect_secret_reference_round_trip(self):
        environment = _environment()

        restored = EnvironmentPersistenceMapper.to_domain(
            EnvironmentPersistenceMapper.to_dto(environment)
        )

        assert restored == environment
        assert restored.configuration["api_token"] == SecretReference("vault", "staging")

    async def test_when_adapter_operations_are_called_expect_domain_values(self):
        dto = _dto()
        adapter = EnvironmentPersistenceAdapter(_Repository(dto))
        environment = _environment()

        saved = await adapter.save(environment)
        by_id = await adapter.find_by_id(dto.id)
        by_key = await adapter.find_by_key(dto.environment_key)
        page = await adapter.find_page(PaginationParams())

        assert saved == environment
        assert by_id == by_key
        assert page.total == 1

    async def test_when_repository_is_called_expect_persistence_operations(self):
        dto = _dto()
        total_result = MagicMock()
        total_result.scalar_one.return_value = 1
        page_result = MagicMock()
        page_result.scalars.return_value.all.return_value = [dto]
        key_result = MagicMock()
        key_result.scalar_one_or_none.return_value = dto
        session = MagicMock()
        session.merge = AsyncMock(return_value=dto)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.get = AsyncMock(return_value=dto)
        session.execute = AsyncMock(side_effect=[key_result, total_result, page_result])
        repository = EnvironmentRepository(_SessionProvider(session))

        assert await repository.save(dto) is dto
        assert await repository.find_by_id(dto.id) is dto
        assert await repository.find_by_key(dto.environment_key) is dto
        assert (
            await repository.find_page(PaginationParams(sort_by="name", order=SortOrder.DESC))
        ).items == (dto,)
        pagination = PaginationParams(sort_by="unsafe")

        with pytest.raises(ValueError, match="unsupported environment sort field"):
            await repository.find_page(pagination)
