from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import Priority, TestCase, TestLevel, TestType
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.authoring.test_cases.persistence.mappers.test_case_persistence_mapper import (  # noqa: E501
    TestCasePersistenceMapper,
)
from test_service.infrastructure.adapters.output.authoring.test_cases.persistence.test_case_persistence_adapter import (  # noqa: E501
    TestCasePersistenceAdapter,
)


def _test_case() -> TestCase:
    return TestCase(
        identifier=uuid4(),
        project_key="IAG",
        test_key="IAG-1",
        version=1,
        name="Gateway test",
        summary="Checks the gateway",
        objective="Receive success",
        test_type=TestType.AUTOMATED,
        test_level=TestLevel.FUNCTIONAL,
        priority=Priority.HIGH,
        definition=Definition(
            schema_version="1.0",
            variables={},
            actions=(Action(identifier="request", action_type="HTTP_REQUEST", configuration={}),),
        ),
        timeout_seconds=30,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        metadata={},
    )


class _Repository:
    def __init__(self, test_case: TestCase | None) -> None:
        self.dto = TestCasePersistenceMapper.to_dto(test_case) if test_case else None
        self.saved = None

    async def save(self, dto):
        self.saved = dto
        return dto

    async def find_by_id(self, _):
        return self.dto

    async def find_latest_version(self, _, __):
        return 4

    async def find_page(self, _, __, ___):
        return Page(
            items=() if self.dto is None else (self.dto,), total=0 if self.dto is None else 1
        )

    async def find_versions(self, _, __, ___, ____):
        return Page(
            items=() if self.dto is None else (self.dto,), total=0 if self.dto is None else 1
        )


class TestTestCasePersistenceAdapter:
    async def test_when_saving_or_finding_test_case_expect_domain_snapshot(self):
        test_case = _test_case()
        repository = _Repository(test_case)
        adapter = TestCasePersistenceAdapter(repository)

        saved = await adapter.save(test_case)
        found = await adapter.find_by_id(test_case.identifier)

        assert saved == test_case
        assert found == test_case
        assert repository.saved.id == test_case.identifier

    async def test_when_test_case_is_absent_expect_none(self):
        result = await TestCasePersistenceAdapter(_Repository(None)).find_by_id(uuid4())

        assert result is None

    async def test_when_versions_and_page_are_requested_expect_mapped_pages(self):
        test_case = _test_case()
        adapter = TestCasePersistenceAdapter(_Repository(test_case))
        pagination = PaginationParams()

        page = await adapter.find_page("IAG", pagination, VersionStatus.ACTIVE)
        versions = await adapter.find_versions("IAG", "IAG-1", pagination)
        latest_version = await adapter.find_latest_version("IAG", "IAG-1")

        assert page.items == (test_case,)
        assert versions.items == (test_case,)
        assert latest_version == 4
