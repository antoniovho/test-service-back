from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from test_service.domain.application.commands.authoring import (
    ActivateTestCaseCommand,
    CreateTestCaseCommand,
    CreateTestCaseVersionCommand,
    DeprecateTestCaseCommand,
)
from test_service.domain.application.queries.authoring import (
    ListTestCasesQuery,
    TestCaseQuery,
    TestCaseVersionsQuery,
)
from test_service.domain.application.services.precondition_reference_resolver import (
    PreconditionReferenceResolver,
)
from test_service.domain.application.services.project_resolver import ProjectResolver
from test_service.domain.application.use_cases.authoring.test_cases.activate_test_case_use_case import (  # noqa: E501
    ActivateTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.create_test_case_use_case import (  # noqa: E501
    CreateTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.create_test_case_version_use_case import (  # noqa: E501
    CreateTestCaseVersionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.deprecate_test_case_use_case import (  # noqa: E501
    DeprecateTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.get_test_case_use_case import (  # noqa: E501
    GetTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.list_test_case_versions_use_case import (  # noqa: E501
    ListTestCaseVersionsUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.list_test_cases_use_case import (  # noqa: E501
    ListTestCasesUseCaseImpl,
)
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.authoring.test_case import (
    Priority,
    TestCase,
    TestLevel,
    TestType,
)
from test_service.domain.model.exceptions.entity_not_found_exception import (
    EntityNotFoundException,
)
from test_service.domain.model.exceptions.test_case_already_exists_exception import (
    TestCaseAlreadyExistsException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.model.projects.project import ProjectStatus


class InMemoryTestCaseRepository:
    def __init__(self, test_cases: tuple[TestCase, ...] = ()) -> None:
        self._test_cases = {test_case.identifier: test_case for test_case in test_cases}

    async def save(self, test_case: TestCase) -> TestCase:
        self._test_cases[test_case.identifier] = test_case
        return test_case

    async def find_by_id(self, identifier: UUID) -> TestCase | None:
        return self._test_cases.get(identifier)

    async def find_latest_version(self, project_key: str, test_key: str) -> int | None:
        versions = (
            test_case
            for test_case in self._test_cases.values()
            if test_case.project_key == project_key and test_case.test_key == test_key
        )
        latest = max(versions, key=lambda test_case: test_case.version, default=None)
        return latest.version if latest is not None else None

    async def find_page(
        self,
        project_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestCase]:
        matching = tuple(
            test_case
            for test_case in self._test_cases.values()
            if test_case.project_key == project_key
            and (status is None or test_case.status is status)
        )
        return Page(
            items=matching[pagination.offset : pagination.offset + pagination.limit],
            total=len(matching),
        )

    async def find_versions(
        self,
        project_key: str,
        test_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestCase]:
        matching = tuple(
            test_case
            for test_case in self._test_cases.values()
            if test_case.project_key == project_key
            and test_case.test_key == test_key
            and (status is None or test_case.status is status)
        )
        return Page(
            items=matching[pagination.offset : pagination.offset + pagination.limit],
            total=len(matching),
        )


class InMemoryPreconditionRepository:
    def __init__(self, preconditions: tuple[Precondition, ...] = ()) -> None:
        self._preconditions = {
            precondition.identifier: precondition for precondition in preconditions
        }

    async def find_by_id(self, identifier: UUID) -> Precondition | None:
        return self._preconditions.get(identifier)


def _definition() -> Definition:
    return Definition(
        variables={},
        actions=(Action(identifier="request", action_type="HTTP_REQUEST", configuration={}),),
    )


def _test_case(**overrides: object) -> TestCase:
    fields = {
        "identifier": uuid4(),
        "project_key": "IAG",
        "test_key": "IAG-001",
        "version": 1,
        "name": "Gateway request succeeds",
        "summary": "Validates a gateway request",
        "objective": "Receive a successful response",
        "test_type": TestType.AUTOMATED,
        "test_level": TestLevel.FUNCTIONAL,
        "priority": Priority.HIGH,
        "definition": _definition(),
        "timeout_seconds": 30,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": "author@example.com",
    }
    fields.update(overrides)
    return TestCase(**fields)


def _precondition(**overrides: object) -> Precondition:
    fields = {
        "identifier": uuid4(),
        "project_key": "IAG",
        "precondition_key": "authenticated",
        "version": 2,
        "name": "Authenticated customer",
        "description": "Customer has a valid session",
        "validation_definition": _definition(),
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": "author@example.com",
    }
    fields.update(overrides)
    return Precondition(**fields)


def _create_command(**overrides: object) -> CreateTestCaseCommand:
    fields = {
        "project_key": "IAG",
        "test_key": "IAG-001",
        "name": "Gateway request succeeds",
        "summary": "Validates a gateway request",
        "objective": "Receive a successful response",
        "test_type": TestType.AUTOMATED,
        "test_level": TestLevel.FUNCTIONAL,
        "priority": Priority.HIGH,
        "definition": _definition(),
        "timeout_seconds": 30,
        "requested_by": "author@example.com",
        "requested_at": datetime(2026, 1, 2, tzinfo=UTC),
    }
    fields.update(overrides)
    return CreateTestCaseCommand(**fields)


def _create_version_command(source_id: UUID) -> CreateTestCaseVersionCommand:
    command = _create_command()
    return CreateTestCaseVersionCommand(
        source_id=source_id,
        project_key=command.project_key,
        name=command.name,
        summary=command.summary,
        objective=command.objective,
        test_type=command.test_type,
        test_level=command.test_level,
        priority=command.priority,
        definition=command.definition,
        timeout_seconds=command.timeout_seconds,
        requested_by=command.requested_by,
        requested_at=command.requested_at,
        preconditions=command.preconditions,
        metadata=command.metadata,
    )


def _project_resolver(
    project: object | None = SimpleNamespace(status=ProjectStatus.ACTIVE),
) -> ProjectResolver:
    return ProjectResolver(SimpleNamespace(find_by_key=lambda key: _async_result(project)))


class TestCreateTestCaseUseCaseImpl:
    async def test_when_command_is_valid_expect_first_draft_with_resolved_preconditions(self):
        precondition = _precondition()
        repository = InMemoryTestCaseRepository()
        resolver = PreconditionReferenceResolver(InMemoryPreconditionRepository((precondition,)))
        use_case = CreateTestCaseUseCaseImpl(repository, resolver, _project_resolver())
        request = _create_command(preconditions=(precondition.identifier,))

        test_case = await use_case.execute(request)

        assert test_case.version == 1
        assert test_case.status is VersionStatus.DRAFT
        assert test_case.preconditions[0].identifier == precondition.identifier
        assert await repository.find_by_id(test_case.identifier) == test_case

    async def test_when_test_key_exists_expect_conflict_with_version_endpoint(self):
        existing = _test_case()
        repository = InMemoryTestCaseRepository((existing,))
        resolver = PreconditionReferenceResolver(InMemoryPreconditionRepository())
        use_case = CreateTestCaseUseCaseImpl(repository, resolver, _project_resolver())
        request = _create_command()

        with pytest.raises(TestCaseAlreadyExistsException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "TEST_CASE_ALREADY_EXISTS"
        assert (
            "/v1/projects/IAG/test-cases/{testCaseId}/versions" in exception.value.error_description
        )

    async def test_when_project_does_not_exist_expect_not_found_without_persisting(self):
        repository = InMemoryTestCaseRepository()
        resolver = PreconditionReferenceResolver(InMemoryPreconditionRepository())
        use_case = CreateTestCaseUseCaseImpl(repository, resolver, _project_resolver(None))
        request = _create_command()

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(request)

        assert await repository.find_latest_version("IAG", "IAG-001") is None


class TestCreateTestCaseVersionUseCaseImpl:
    async def test_when_source_exists_expect_next_draft_version_persisted(self):
        source = _test_case(version=3)
        repository = InMemoryTestCaseRepository((source,))
        resolver = PreconditionReferenceResolver(InMemoryPreconditionRepository())
        use_case = CreateTestCaseVersionUseCaseImpl(repository, resolver)
        request = _create_version_command(source.identifier)

        version = await use_case.execute(request)

        assert version.identifier != source.identifier
        assert version.version == 4
        assert version.status is VersionStatus.DRAFT
        assert version.project_key == source.project_key
        assert version.test_key == source.test_key

    async def test_when_source_does_not_exist_expect_not_found_exception(self):
        resolver = PreconditionReferenceResolver(InMemoryPreconditionRepository())
        use_case = CreateTestCaseVersionUseCaseImpl(InMemoryTestCaseRepository(), resolver)
        request = _create_version_command(uuid4())

        with pytest.raises(EntityNotFoundException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "ENTITY_NOT_FOUND"
        assert (
            exception.value.error_description
            == f"Test case '{request.source_id}' was not found in project '{request.project_key}'."
        )

    async def test_when_source_belongs_to_another_project_expect_not_found_exception(self):
        source = _test_case(project_key="OTHER")
        resolver = PreconditionReferenceResolver(InMemoryPreconditionRepository())
        use_case = CreateTestCaseVersionUseCaseImpl(InMemoryTestCaseRepository((source,)), resolver)
        request = _create_version_command(source.identifier)

        with pytest.raises(EntityNotFoundException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "ENTITY_NOT_FOUND"

    async def test_when_newer_version_exists_expect_version_after_latest_persisted(self):
        source = _test_case(version=2)
        latest = _test_case(identifier=uuid4(), version=4)
        repository = InMemoryTestCaseRepository((source, latest))
        resolver = PreconditionReferenceResolver(InMemoryPreconditionRepository())
        use_case = CreateTestCaseVersionUseCaseImpl(repository, resolver)
        request = _create_version_command(source.identifier)

        version = await use_case.execute(request)

        assert version.version == 5


class TestGetTestCaseUseCaseImpl:
    async def test_when_snapshot_exists_expect_snapshot_returned(self):
        test_case = _test_case()
        use_case = GetTestCaseUseCaseImpl(InMemoryTestCaseRepository((test_case,)))

        result = await use_case.execute(TestCaseQuery("IAG", test_case.identifier))

        assert result == test_case

    async def test_when_snapshot_does_not_exist_expect_not_found_exception(self):
        use_case = GetTestCaseUseCaseImpl(InMemoryTestCaseRepository())

        with pytest.raises(EntityNotFoundException) as exception:
            await use_case.execute(TestCaseQuery("IAG", uuid4()))

        assert exception.value.code == "ENTITY_NOT_FOUND"

    async def test_when_snapshot_belongs_to_another_project_expect_not_found_exception(self):
        test_case = _test_case(project_key="OTHER")
        use_case = GetTestCaseUseCaseImpl(InMemoryTestCaseRepository((test_case,)))

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(TestCaseQuery("IAG", test_case.identifier))


class TestLifecycleTestCaseUseCases:
    async def test_when_draft_is_activated_expect_active_snapshot_persisted(self):
        test_case = _test_case()
        repository = InMemoryTestCaseRepository((test_case,))
        use_case = ActivateTestCaseUseCaseImpl(repository)

        activated = await use_case.execute(ActivateTestCaseCommand("IAG", test_case.identifier))

        assert activated.status is VersionStatus.ACTIVE
        assert await repository.find_by_id(test_case.identifier) == activated

    async def test_when_active_is_deprecated_expect_deprecated_snapshot_persisted(self):
        test_case = _test_case().activate()
        repository = InMemoryTestCaseRepository((test_case,))
        use_case = DeprecateTestCaseUseCaseImpl(repository)

        deprecated = await use_case.execute(DeprecateTestCaseCommand("IAG", test_case.identifier))

        assert deprecated.status is VersionStatus.DEPRECATED

    @pytest.mark.parametrize(
        ("use_case_class", "command_class"),
        [
            (ActivateTestCaseUseCaseImpl, ActivateTestCaseCommand),
            (DeprecateTestCaseUseCaseImpl, DeprecateTestCaseCommand),
        ],
        ids=["activate", "deprecate"],
    )
    async def test_when_lifecycle_snapshot_belongs_to_another_project_expect_not_found_exception(
        self, use_case_class, command_class
    ):
        test_case = _test_case(project_key="OTHER")
        repository = InMemoryTestCaseRepository((test_case,))
        use_case = use_case_class(repository)
        request = command_class("IAG", test_case.identifier)

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(request)

        assert await repository.find_by_id(test_case.identifier) == test_case


class TestListTestCaseUseCases:
    async def test_when_project_matches_expect_filtered_test_case_page(self):
        test_case = _test_case()
        other_project_case = _test_case(project_key="OTHER")
        use_case = ListTestCasesUseCaseImpl(
            InMemoryTestCaseRepository((test_case, other_project_case)), _project_resolver()
        )

        page = await use_case.execute(ListTestCasesQuery("IAG", PaginationParams()))

        assert page.items == (test_case,)
        assert page.total == 1

    async def test_when_key_matches_expect_version_page(self):
        first = _test_case(version=1)
        second = _test_case(identifier=uuid4(), version=2)
        other_key = _test_case(identifier=uuid4(), test_key="IAG-002")
        use_case = ListTestCaseVersionsUseCaseImpl(
            InMemoryTestCaseRepository((first, second, other_key)), _project_resolver()
        )

        page = await use_case.execute(TestCaseVersionsQuery("IAG", "IAG-001", PaginationParams()))

        assert page.items == (first, second)
        assert page.total == 2


async def _async_result(value):
    return value
