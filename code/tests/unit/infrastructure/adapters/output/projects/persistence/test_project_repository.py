from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from test_service.domain.commons.pagination import PaginationParams, SortOrder
from test_service.infrastructure.adapters.output.projects.persistence.dtos.project_dto import (
    ProjectDTO,
)
from test_service.infrastructure.adapters.output.projects.persistence.repositories.project_repository import (  # noqa: E501
    ProjectRepository,
)


class _SessionProvider:
    def __init__(self, session: MagicMock) -> None:
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session


def _dto(key: str = "IAG") -> ProjectDTO:
    return ProjectDTO(
        key=key,
        name="AI Gateway",
        status="ACTIVE",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="admin@example.com",
        deleted_at=None,
        deleted_by=None,
    )


class TestProjectRepository:
    async def test_when_saving_project_expect_merged_committed_and_refreshed(self):
        project = _dto()
        session = MagicMock()
        session.merge = AsyncMock(return_value=project)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ProjectRepository(_SessionProvider(session))

        result = await repository.save(project)

        assert result is project
        session.merge.assert_awaited_once_with(project)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(project)

    async def test_when_project_exists_expect_dto_returned(self):
        project = _dto()
        session = MagicMock()
        session.get = AsyncMock(return_value=project)
        repository = ProjectRepository(_SessionProvider(session))

        result = await repository.find_by_key(project.key)

        assert result is project
        session.get.assert_awaited_once_with(ProjectDTO, project.key)

    async def test_when_project_is_absent_expect_none(self):
        session = MagicMock()
        session.get = AsyncMock(return_value=None)
        repository = ProjectRepository(_SessionProvider(session))

        result = await repository.find_by_key("UNKNOWN")

        assert result is None

    async def test_when_page_is_requested_expect_ordered_dtos_and_total(self):
        first, second = _dto("IAG"), _dto("ZAR")
        total_result = MagicMock()
        total_result.scalar_one.return_value = 2
        page_result = MagicMock()
        page_result.scalars.return_value.all.return_value = [first, second]
        session = MagicMock()
        session.execute = AsyncMock(side_effect=[total_result, page_result])
        repository = ProjectRepository(_SessionProvider(session))

        page = await repository.find_page(
            PaginationParams(offset=0, limit=10, sort_by="name", order=SortOrder.DESC)
        )

        assert page.items == (first, second)
        assert page.total == 2
        assert session.execute.await_count == 2

    async def test_when_sort_field_is_unsupported_expect_value_error(self):
        repository = ProjectRepository(_SessionProvider(MagicMock()))
        pagination = PaginationParams(sort_by="unsafe")

        with pytest.raises(ValueError, match="unsupported project sort field: unsafe"):
            await repository.find_page(pagination)
