from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from test_service.domain.commons.pagination import PaginationParams, SortOrder
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.dtos.precondition_dto import (  # noqa: E501
    PreconditionDTO,
)
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.repositories.precondition_repository import (  # noqa: E501
    PreconditionRepository,
)


class _SessionProvider:
    def __init__(self, session: MagicMock) -> None:
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session


def _dto() -> PreconditionDTO:
    return PreconditionDTO(
        id=uuid4(),
        project_key="IAG",
        precondition_key="authenticated",
        version=1,
        name="Authenticated user",
        description="User has a session",
        validation_definition={"schema_version": "1.0", "variables": {}, "actions": []},
        status="DRAFT",
        metadata_={},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
    )


class TestPreconditionRepository:
    async def test_when_saving_precondition_expect_persisted_dto(self):
        dto = _dto()
        session = MagicMock()
        session.merge = AsyncMock(return_value=dto)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        saved = await PreconditionRepository(_SessionProvider(session)).save(dto)

        assert saved is dto
        session.merge.assert_awaited_once_with(dto)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(dto)

    async def test_when_precondition_exists_expect_dto_returned(self):
        dto = _dto()
        result = MagicMock()
        result.scalar_one_or_none.return_value = dto
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        found = await PreconditionRepository(_SessionProvider(session)).find_by_id(dto.id)

        assert found is dto
        session.execute.assert_awaited_once()

    async def test_when_precondition_is_absent_expect_none(self):
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        found = await PreconditionRepository(_SessionProvider(session)).find_by_id(uuid4())

        assert found is None

    async def test_when_latest_version_is_requested_expect_database_maximum(self):
        result = MagicMock()
        result.scalar_one.return_value = 6
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        latest_version = await PreconditionRepository(
            _SessionProvider(session)
        ).find_latest_version("IAG", "authenticated")

        assert latest_version == 6

    async def test_when_pages_are_requested_expect_dtos_and_total(self):
        dto = _dto()
        total_result = MagicMock()
        total_result.scalar_one.return_value = 1
        page_result = MagicMock()
        page_result.scalars.return_value.all.return_value = [dto]
        session = MagicMock()
        session.execute = AsyncMock(
            side_effect=[total_result, page_result, total_result, page_result]
        )
        repository = PreconditionRepository(_SessionProvider(session))
        pagination = PaginationParams(sort_by="version", order=SortOrder.DESC)

        page = await repository.find_page("IAG", pagination, VersionStatus.DRAFT)
        versions = await repository.find_versions("IAG", "authenticated", pagination, None)

        assert page.items == (dto,)
        assert page.total == 1
        assert versions.items == (dto,)

    async def test_when_sort_field_is_unsupported_expect_value_error(self):
        repository = PreconditionRepository(_SessionProvider(MagicMock()))
        page_request = repository.find_page("IAG", PaginationParams(sort_by="unsafe"), None)

        with pytest.raises(ValueError, match="unsupported precondition sort field: unsafe"):
            await page_request
