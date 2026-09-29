from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from test_service.domain.commons.pagination import PaginationParams, SortOrder
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.authoring.test_cases.persistence.dtos.test_case_dto import (  # noqa: E501
    TestCaseDTO,
)
from test_service.infrastructure.adapters.output.authoring.test_cases.persistence.repositories.test_case_repository import (  # noqa: E501
    TestCaseRepository,
)


class _SessionProvider:
    def __init__(self, session: MagicMock) -> None:
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session


def _dto() -> TestCaseDTO:
    return TestCaseDTO(
        id=uuid4(),
        project_key="IAG",
        test_key="IAG-1",
        version=2,
        name="Gateway test",
        summary="Checks the gateway",
        objective="Receive success",
        test_type="AUTOMATED",
        test_level="FUNCTIONAL",
        priority="HIGH",
        status="DRAFT",
        definition={"schema_version": "1.0", "variables": {}, "actions": []},
        timeout_seconds=30,
        metadata_={},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
    )


class TestTestCaseRepository:
    async def test_when_saving_or_finding_test_case_expect_loaded_dto(self):
        dto = _dto()
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = dto
        session = MagicMock()
        session.merge = AsyncMock(return_value=dto)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock(return_value=query_result)
        repository = TestCaseRepository(_SessionProvider(session))

        saved = await repository.save(dto)
        found = await repository.find_by_id(dto.id)

        assert saved is dto
        assert found is dto
        session.merge.assert_awaited_once_with(dto)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(dto)

    async def test_when_latest_version_is_requested_expect_database_maximum(self):
        result = MagicMock()
        result.scalar_one.return_value = 6
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        latest_version = await TestCaseRepository(_SessionProvider(session)).find_latest_version(
            "IAG", "IAG-1"
        )

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
        repository = TestCaseRepository(_SessionProvider(session))
        pagination = PaginationParams(sort_by="version", order=SortOrder.DESC)

        page = await repository.find_page("IAG", pagination, VersionStatus.DRAFT)
        versions = await repository.find_versions("IAG", "IAG-1", pagination, None)

        assert page.items == (dto,)
        assert page.total == 1
        assert versions.items == (dto,)

    async def test_when_sort_field_is_unsupported_expect_value_error(self):
        repository = TestCaseRepository(_SessionProvider(MagicMock()))
        page_request = repository.find_page("IAG", PaginationParams(sort_by="unsafe"), None)

        with pytest.raises(ValueError, match="unsupported test case sort field: unsafe"):
            await page_request
