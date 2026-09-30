from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from test_service.domain.application.commands.composition import (
    ActivateTestSetCommand,
    CreateTestSetCommand,
    CreateTestSetVersionCommand,
)
from test_service.domain.application.queries.composition import (
    ListTestSetsQuery,
    TestSetQuery,
)
from test_service.domain.application.services.project_resolver import ProjectResolver
from test_service.domain.application.services.test_case_snapshot_resolver import (
    TestCaseSnapshotResolver,
)
from test_service.domain.application.use_cases.composition.test_sets.activate_test_set_use_case import (  # noqa: E501
    ActivateTestSetUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.create_test_set_use_case import (  # noqa: E501
    CreateTestSetUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.create_test_set_version_use_case import (  # noqa: E501
    CreateTestSetVersionUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.get_test_set_use_case import (  # noqa: E501
    GetTestSetUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.list_test_sets_use_case import (  # noqa: E501
    ListTestSetsUseCaseImpl,
)
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import Priority, TestCase, TestLevel, TestType
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.test_set_already_exists_exception import (
    TestSetAlreadyExistsException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.model.projects.project import ProjectStatus


class _TestSetRepository:
    def __init__(self, snapshots: tuple[TestSet, ...] = ()) -> None:
        self.snapshots = {snapshot.identifier: snapshot for snapshot in snapshots}

    async def save(self, snapshot: TestSet) -> TestSet:
        self.snapshots[snapshot.identifier] = snapshot
        return snapshot

    async def find_by_id(self, identifier: UUID) -> TestSet | None:
        return self.snapshots.get(identifier)

    async def find_latest_version(self, project_key: str, set_key: str) -> int | None:
        versions = [
            snapshot.version
            for snapshot in self.snapshots.values()
            if snapshot.project_key == project_key and snapshot.set_key == set_key
        ]
        return max(versions, default=None)

    async def find_page(self, project_key, pagination, status=None):
        snapshots = tuple(
            snapshot
            for snapshot in self.snapshots.values()
            if snapshot.project_key == project_key and (status is None or snapshot.status is status)
        )
        return Page(
            snapshots[pagination.offset : pagination.offset + pagination.limit], len(snapshots)
        )

    async def find_versions(self, project_key, set_key, pagination, status=None):
        snapshots = tuple(
            snapshot
            for snapshot in self.snapshots.values()
            if snapshot.project_key == project_key
            and snapshot.set_key == set_key
            and (status is None or snapshot.status is status)
        )
        return Page(
            snapshots[pagination.offset : pagination.offset + pagination.limit], len(snapshots)
        )


class _TestCaseRepository:
    def __init__(self, test_case: TestCase) -> None:
        self.test_case = test_case

    async def find_by_id(self, identifier: UUID) -> TestCase | None:
        return self.test_case if identifier == self.test_case.identifier else None

    async def save(self, snapshot: TestCase) -> TestCase:
        self.test_case = snapshot
        return snapshot

    async def find_latest_version(self, project_key: str, test_key: str) -> int | None:
        if self.test_case.project_key == project_key and self.test_case.test_key == test_key:
            return self.test_case.version
        return None

    async def find_page(
        self, project_key: str, pagination: PaginationParams, status: VersionStatus | None = None
    ) -> Page[TestCase]:
        snapshots = (
            (self.test_case,)
            if self.test_case.project_key == project_key
            and (status is None or self.test_case.status is status)
            else ()
        )
        return Page(
            snapshots[pagination.offset : pagination.offset + pagination.limit], len(snapshots)
        )

    async def find_versions(
        self,
        project_key: str,
        test_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestCase]:
        snapshots = (
            (self.test_case,)
            if self.test_case.project_key == project_key
            and self.test_case.test_key == test_key
            and (status is None or self.test_case.status is status)
            else ()
        )
        return Page(
            snapshots[pagination.offset : pagination.offset + pagination.limit], len(snapshots)
        )


def _test_case(project_key: str = "IAG") -> TestCase:
    return TestCase(
        identifier=uuid4(),
        project_key=project_key,
        test_key="IAG-1",
        version=1,
        name="Gateway",
        summary="Gateway",
        objective="Success",
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
    )


def _command(item: UUID) -> CreateTestSetCommand:
    return CreateTestSetCommand(
        "IAG",
        "checkout",
        "Checkout",
        (item,),
        "author@example.test",
        datetime(2026, 1, 2, tzinfo=UTC),
    )


def _project_resolver() -> ProjectResolver:
    return ProjectResolver(
        SimpleNamespace(
            find_by_key=lambda key: _async_result(SimpleNamespace(status=ProjectStatus.ACTIVE))
        )
    )


class TestTestSetUseCases:
    async def test_when_creating_valid_set_expect_first_draft_persisted(self):
        test_case = _test_case()
        repository = _TestSetRepository()
        use_case = CreateTestSetUseCaseImpl(
            repository,
            TestCaseSnapshotResolver(_TestCaseRepository(test_case)),
            _project_resolver(),
        )

        result = await use_case.execute(_command(test_case.identifier))

        assert result.version == 1
        assert result.items == (test_case.identifier,)
        assert result.status is VersionStatus.DRAFT

    async def test_when_key_already_exists_expect_conflict(self):
        test_case = _test_case()
        existing = TestSet(
            uuid4(),
            "IAG",
            "checkout",
            1,
            "Checkout",
            (test_case.identifier,),
            datetime(2026, 1, 1, tzinfo=UTC),
            "author@example.test",
        )
        use_case = CreateTestSetUseCaseImpl(
            _TestSetRepository((existing,)),
            TestCaseSnapshotResolver(_TestCaseRepository(test_case)),
            _project_resolver(),
        )
        command = _command(test_case.identifier)

        with pytest.raises(TestSetAlreadyExistsException):
            await use_case.execute(command)

    async def test_when_versioning_project_scoped_source_expect_next_version(self):
        test_case = _test_case()
        source = TestSet(
            uuid4(),
            "IAG",
            "checkout",
            2,
            "Checkout",
            (test_case.identifier,),
            datetime(2026, 1, 1, tzinfo=UTC),
            "author@example.test",
        )
        use_case = CreateTestSetVersionUseCaseImpl(
            _TestSetRepository((source,)), TestCaseSnapshotResolver(_TestCaseRepository(test_case))
        )
        request = CreateTestSetVersionCommand(
            source.identifier,
            "IAG",
            "ignored",
            "Updated",
            (test_case.identifier,),
            "author@example.test",
            datetime(2026, 1, 2, tzinfo=UTC),
        )

        result = await use_case.execute(request)

        assert result.version == 3
        assert result.set_key == source.set_key

    async def test_when_snapshot_is_outside_project_expect_not_found(self):
        test_case = _test_case()
        snapshot = TestSet(
            uuid4(),
            "OTHER",
            "checkout",
            1,
            "Checkout",
            (test_case.identifier,),
            datetime(2026, 1, 1, tzinfo=UTC),
            "author@example.test",
        )
        use_case = GetTestSetUseCaseImpl(_TestSetRepository((snapshot,)))
        query = TestSetQuery("IAG", snapshot.identifier)

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(query)

    async def test_when_lifecycle_and_list_are_requested_expect_project_scoped_results(self):
        test_case = _test_case()
        snapshot = TestSet(
            uuid4(),
            "IAG",
            "checkout",
            1,
            "Checkout",
            (test_case.identifier,),
            datetime(2026, 1, 1, tzinfo=UTC),
            "author@example.test",
        )
        repository = _TestSetRepository((snapshot,))

        activated = await ActivateTestSetUseCaseImpl(repository).execute(
            ActivateTestSetCommand("IAG", snapshot.identifier)
        )
        page = await ListTestSetsUseCaseImpl(repository, _project_resolver()).execute(
            ListTestSetsQuery("IAG", PaginationParams())
        )

        assert activated.status is VersionStatus.ACTIVE
        assert page.items == (activated,)


async def _async_result(value):
    return value
