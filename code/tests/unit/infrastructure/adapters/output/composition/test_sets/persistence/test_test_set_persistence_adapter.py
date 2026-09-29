from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.composition.test_sets.persistence.mappers.test_set_persistence_mapper import (  # noqa: E501
    TestSetPersistenceMapper,
)
from test_service.infrastructure.adapters.output.composition.test_sets.persistence.test_set_persistence_adapter import (  # noqa: E501
    TestSetPersistenceAdapter,
)


def _test_set() -> TestSet:
    return TestSet(
        uuid4(),
        "IAG",
        "checkout",
        1,
        "Checkout",
        (uuid4(),),
        datetime(2026, 1, 1, tzinfo=UTC),
        "author@example.test",
    )


class _Repository:
    def __init__(self, test_set: TestSet | None) -> None:
        self.dto = TestSetPersistenceMapper.to_dto(test_set) if test_set else None

    async def save(self, dto):
        return dto

    async def find_by_id(self, _):
        return self.dto

    async def find_latest_version(self, _, __):
        return 4

    async def find_page(self, _, __, ___):
        return Page(() if self.dto is None else (self.dto,), 0 if self.dto is None else 1)

    async def find_versions(self, _, __, ___, ____):
        return Page(() if self.dto is None else (self.dto,), 0 if self.dto is None else 1)


class TestTestSetPersistenceAdapter:
    async def test_when_saving_or_finding_test_set_expect_domain_snapshot(self):
        test_set = _test_set()
        adapter = TestSetPersistenceAdapter(_Repository(test_set))

        saved = await adapter.save(test_set)
        found = await adapter.find_by_id(test_set.identifier)

        assert saved == test_set
        assert found == test_set

    async def test_when_test_set_is_absent_expect_none(self):
        result = await TestSetPersistenceAdapter(_Repository(None)).find_by_id(uuid4())

        assert result is None

    async def test_when_versions_and_page_are_requested_expect_mapped_pages(self):
        test_set = _test_set()
        adapter = TestSetPersistenceAdapter(_Repository(test_set))
        pagination = PaginationParams()

        page = await adapter.find_page("IAG", pagination, VersionStatus.ACTIVE)
        versions = await adapter.find_versions("IAG", "checkout", pagination)
        latest = await adapter.find_latest_version("IAG", "checkout")

        assert page.items == (test_set,)
        assert versions.items == (test_set,)
        assert latest == 4
