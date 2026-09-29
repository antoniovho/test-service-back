from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from test_service.domain.commons.pagination import PaginationParams, SortOrder
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.dtos.test_plan_dto import (  # noqa: E501
    TestPlanDTO,
)
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.repositories.test_plan_repository import (  # noqa: E501
    TestPlanRepository,
)


class _SessionProvider:
    def __init__(self, session: MagicMock) -> None:
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session


def _dto() -> TestPlanDTO:
    return TestPlanDTO(
        id=uuid4(),
        project_key="IAG",
        plan_key="checkout-nightly",
        version=1,
        name="Checkout nightly",
        description="Nightly regression",
        status="DRAFT",
        execution_mode="SEQUENTIAL",
        max_parallelism=None,
        timeout_seconds=900,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
    )


class TestTestPlanRepository:
    async def test_when_saving_or_finding_test_plan_expect_loaded_dto(self):
        dto = _dto()
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = dto
        session = MagicMock()
        session.merge = AsyncMock(return_value=dto)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock(return_value=query_result)
        repository = TestPlanRepository(_SessionProvider(session))

        saved = await repository.save(dto)
        found = await repository.find_by_id(dto.id)

        assert saved is dto
        assert found is dto
        session.refresh.assert_awaited_once_with(
            dto,
            attribute_names=["test_set_links", "test_case_links", "exclusion_links"],
        )

    async def test_when_latest_version_is_requested_expect_database_maximum(self):
        result = MagicMock()
        result.scalar_one.return_value = 6
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        latest = await TestPlanRepository(_SessionProvider(session)).find_latest_version(
            "IAG", "checkout-nightly"
        )

        assert latest == 6

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
        repository = TestPlanRepository(_SessionProvider(session))
        pagination = PaginationParams(sort_by="version", order=SortOrder.DESC)

        page = await repository.find_page("IAG", pagination, VersionStatus.DRAFT)
        versions = await repository.find_versions("IAG", "checkout-nightly", pagination, None)

        assert page.items == (dto,)
        assert page.total == 1
        assert versions.items == (dto,)

    async def test_when_sort_field_is_unsupported_expect_value_error(self):
        request = TestPlanRepository(_SessionProvider(MagicMock())).find_page(
            "IAG", PaginationParams(sort_by="unsafe"), None
        )

        with pytest.raises(ValueError, match="unsupported test plan sort field: unsafe"):
            await request
