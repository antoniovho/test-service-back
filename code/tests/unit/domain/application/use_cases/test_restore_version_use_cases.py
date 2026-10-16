from dataclasses import fields
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from test_service.domain.application.commands.authoring import (
    RestorePreconditionCommand,
    RestoreTestCaseCommand,
)
from test_service.domain.application.commands.composition import (
    RestoreTestPlanCommand,
    RestoreTestSetCommand,
)
from test_service.domain.application.use_cases.authoring.preconditions.restore_precondition_use_case import (  # noqa: E501
    RestorePreconditionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.restore_test_case_use_case import (  # noqa: E501
    RestoreTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_plans.restore_test_plan_use_case import (  # noqa: E501
    RestoreTestPlanUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.restore_test_set_use_case import (  # noqa: E501
    RestoreTestSetUseCaseImpl,
)
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.authoring.test_case import Priority, TestCase, TestLevel, TestType
from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.invalid_lifecycle_transition_exception import (
    InvalidLifecycleTransitionException,
)
from test_service.domain.model.lifecycle import VersionStatus


class _Repository:
    def __init__(self, source, latest: int | None = 4) -> None:
        self.source = source
        self.latest = latest
        self.saved = None

    async def find_by_id(self, _identifier):
        return self.source

    async def find_latest_version(self, _project_key, _logical_key):
        return self.latest

    async def save(self, value):
        self.saved = value
        return value


def _definition() -> Definition:
    return Definition(
        schema_version="1.0",
        variables={"gateway_base_url": "https://gateway.example.test"},
        actions=(Action(identifier="request", action_type="HTTP_REQUEST", configuration={}),),
    )


def _test_case(status: VersionStatus) -> TestCase:
    return TestCase(
        uuid4(),
        "IAG",
        "IAG-1",
        2,
        "Gateway",
        "Summary",
        "Objective",
        TestType.AUTOMATED,
        TestLevel.FUNCTIONAL,
        Priority.HIGH,
        _definition(),
        30,
        datetime(2026, 1, 1, tzinfo=UTC),
        "original@example.test",
        status=status,
        metadata={"source": "historic"},
    )


def _precondition(status: VersionStatus) -> Precondition:
    return Precondition(
        uuid4(),
        "IAG",
        "authenticated",
        2,
        "Authenticated",
        "Session is valid",
        _definition(),
        datetime(2026, 1, 1, tzinfo=UTC),
        "original@example.test",
        status,
        {"source": "historic"},
    )


def _test_set(status: VersionStatus) -> TestSet:
    return TestSet(
        uuid4(),
        "IAG",
        "checkout",
        2,
        "Checkout",
        (uuid4(),),
        datetime(2026, 1, 1, tzinfo=UTC),
        "original@example.test",
        "Historic set",
        status,
    )


def _test_plan(status: VersionStatus) -> TestPlan:
    return TestPlan(
        uuid4(),
        "IAG",
        "nightly",
        2,
        "Nightly",
        ExecutionMode.SEQUENTIAL,
        120,
        datetime(2026, 1, 1, tzinfo=UTC),
        "original@example.test",
        test_set_ids=(uuid4(),),
        test_case_ids=(uuid4(),),
        description="Historic plan",
        status=status,
    )


@pytest.mark.parametrize(
    ("source_factory", "command_type", "use_case_type", "logical_key"),
    [
        (_test_case, RestoreTestCaseCommand, RestoreTestCaseUseCaseImpl, "test_key"),
        (
            _precondition,
            RestorePreconditionCommand,
            RestorePreconditionUseCaseImpl,
            "precondition_key",
        ),
        (_test_set, RestoreTestSetCommand, RestoreTestSetUseCaseImpl, "set_key"),
        (_test_plan, RestoreTestPlanCommand, RestoreTestPlanUseCaseImpl, "plan_key"),
    ],
)
async def test_when_deprecated_snapshot_is_restored_expect_next_draft_clone(
    source_factory, command_type, use_case_type, logical_key
):
    source = source_factory(VersionStatus.DEPRECATED)
    repository = _Repository(source)
    resolver = SimpleNamespace(resolve_active=AsyncMock())
    requested_at = datetime(2026, 2, 1, tzinfo=UTC)

    restored = await use_case_type(repository, resolver).execute(
        command_type("IAG", source.identifier, "restorer@example.test", requested_at)
    )

    assert restored.identifier != source.identifier
    assert restored.version == 5
    assert restored.status is VersionStatus.DRAFT
    assert restored.created_by == "restorer@example.test"
    assert restored.created_at == requested_at
    for field in fields(source):
        if field.name in {"identifier", "version", "created_at", "created_by", "status"}:
            continue
        assert getattr(restored, field.name) == getattr(source, field.name)
    assert getattr(restored, logical_key) == getattr(source, logical_key)
    assert repository.saved is restored
    resolver.resolve_active.assert_awaited_once_with("IAG")


@pytest.mark.parametrize(
    ("source_factory", "command_type", "use_case_type"),
    [
        (_test_case, RestoreTestCaseCommand, RestoreTestCaseUseCaseImpl),
        (_precondition, RestorePreconditionCommand, RestorePreconditionUseCaseImpl),
        (_test_set, RestoreTestSetCommand, RestoreTestSetUseCaseImpl),
        (_test_plan, RestoreTestPlanCommand, RestoreTestPlanUseCaseImpl),
    ],
)
async def test_when_snapshot_is_not_deprecated_expect_restore_rejected(
    source_factory, command_type, use_case_type
):
    source = source_factory(VersionStatus.ACTIVE)
    repository = _Repository(source)

    with pytest.raises(InvalidLifecycleTransitionException, match=str(source.identifier)):
        await use_case_type(repository, SimpleNamespace(resolve_active=AsyncMock())).execute(
            command_type("IAG", source.identifier, "restorer@example.test", datetime.now(UTC))
        )

    assert repository.saved is None


@pytest.mark.parametrize(
    ("source_factory", "command_type", "use_case_type"),
    [
        (_test_case, RestoreTestCaseCommand, RestoreTestCaseUseCaseImpl),
        (_precondition, RestorePreconditionCommand, RestorePreconditionUseCaseImpl),
        (_test_set, RestoreTestSetCommand, RestoreTestSetUseCaseImpl),
        (_test_plan, RestoreTestPlanCommand, RestoreTestPlanUseCaseImpl),
    ],
)
async def test_when_no_later_version_exists_expect_source_version_plus_one(
    source_factory, command_type, use_case_type
):
    source = source_factory(VersionStatus.DEPRECATED)
    repository = _Repository(source, latest=None)

    restored = await use_case_type(repository, SimpleNamespace(resolve_active=AsyncMock())).execute(
        command_type("IAG", source.identifier, "restorer@example.test", datetime.now(UTC))
    )

    assert restored.version == source.version + 1


@pytest.mark.parametrize(
    ("source_factory", "command_type", "use_case_type"),
    [
        (_test_case, RestoreTestCaseCommand, RestoreTestCaseUseCaseImpl),
        (_precondition, RestorePreconditionCommand, RestorePreconditionUseCaseImpl),
        (_test_set, RestoreTestSetCommand, RestoreTestSetUseCaseImpl),
        (_test_plan, RestoreTestPlanCommand, RestoreTestPlanUseCaseImpl),
    ],
)
async def test_when_source_belongs_to_another_project_expect_not_found(
    source_factory, command_type, use_case_type
):
    source = source_factory(VersionStatus.DEPRECATED)
    repository = _Repository(source)

    with pytest.raises(EntityNotFoundException, match="project 'OTHER'"):
        await use_case_type(repository, SimpleNamespace(resolve_active=AsyncMock())).execute(
            command_type("OTHER", source.identifier, "restorer@example.test", datetime.now(UTC))
        )

    assert repository.saved is None


@pytest.mark.parametrize(
    ("command_type", "use_case_type"),
    [
        (RestoreTestCaseCommand, RestoreTestCaseUseCaseImpl),
        (RestorePreconditionCommand, RestorePreconditionUseCaseImpl),
        (RestoreTestSetCommand, RestoreTestSetUseCaseImpl),
        (RestoreTestPlanCommand, RestoreTestPlanUseCaseImpl),
    ],
)
async def test_when_restore_source_does_not_exist_expect_not_found(command_type, use_case_type):
    source_id = uuid4()
    repository = _Repository(None)

    with pytest.raises(EntityNotFoundException, match=str(source_id)):
        await use_case_type(repository, SimpleNamespace(resolve_active=AsyncMock())).execute(
            command_type("IAG", source_id, "restorer@example.test", datetime.now(UTC))
        )

    assert repository.saved is None
