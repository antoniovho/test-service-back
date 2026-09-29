from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.mappers.test_plan_persistence_mapper import (  # noqa: E501
    TestPlanPersistenceMapper,
)
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.test_plan_persistence_adapter import (  # noqa: E501
    TestPlanPersistenceAdapter,
)


def _test_plan() -> TestPlan:
    return TestPlan(
        uuid4(),
        "IAG",
        "checkout-nightly",
        1,
        "Checkout nightly",
        ExecutionMode.SEQUENTIAL,
        900,
        datetime(2026, 1, 1, tzinfo=UTC),
        "author@example.test",
        test_case_ids=(uuid4(),),
    )


class _Repository:
    def __init__(self, test_plan: TestPlan | None) -> None:
        self.dto = TestPlanPersistenceMapper.to_dto(test_plan) if test_plan else None

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


class TestTestPlanPersistenceAdapter:
    async def test_when_saving_or_finding_test_plan_expect_domain_snapshot(self):
        test_plan = _test_plan()
        adapter = TestPlanPersistenceAdapter(_Repository(test_plan))

        saved = await adapter.save(test_plan)
        found = await adapter.find_by_id(test_plan.identifier)

        assert saved == test_plan
        assert found == test_plan

    async def test_when_test_plan_is_absent_expect_none(self):
        result = await TestPlanPersistenceAdapter(_Repository(None)).find_by_id(uuid4())

        assert result is None

    async def test_when_versions_and_page_are_requested_expect_mapped_pages(self):
        test_plan = _test_plan()
        adapter = TestPlanPersistenceAdapter(_Repository(test_plan))
        pagination = PaginationParams()

        page = await adapter.find_page("IAG", pagination, VersionStatus.ACTIVE)
        versions = await adapter.find_versions("IAG", "checkout-nightly", pagination)
        latest = await adapter.find_latest_version("IAG", "checkout-nightly")

        assert page.items == (test_plan,)
        assert versions.items == (test_plan,)
        assert latest == 4
