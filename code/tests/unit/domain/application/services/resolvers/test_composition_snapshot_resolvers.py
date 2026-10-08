from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from test_service.domain.application.services.resolvers.test_case_snapshot_resolver import (
    TestCaseSnapshotResolver,
)
from test_service.domain.application.services.resolvers.test_set_snapshot_resolver import (
    TestSetSnapshotResolver,
)
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import (
    Priority,
    TestCase,
    TestLevel,
    TestType,
)
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.exceptions.entity_not_found_exception import (
    EntityNotFoundException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)


def _test_case(status: VersionStatus) -> TestCase:
    return TestCase(
        identifier=uuid4(),
        project_key="IAG",
        test_key="checkout",
        version=1,
        name="Checkout",
        summary="Checks checkout",
        objective="Complete checkout",
        test_type=TestType.AUTOMATED,
        test_level=TestLevel.FUNCTIONAL,
        priority=Priority.HIGH,
        definition=Definition(
            variables={},
            actions=(Action("request", "HTTP", {"url": "https://example.test"}),),
        ),
        timeout_seconds=60,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        status=status,
    )


def _test_set(status: VersionStatus) -> TestSet:
    return TestSet(
        identifier=uuid4(),
        project_key="IAG",
        set_key="checkout",
        version=1,
        name="Checkout",
        items=(uuid4(),),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        status=status,
    )


class TestCompositionSnapshotResolvers:
    @pytest.mark.parametrize("status", (VersionStatus.DRAFT, VersionStatus.DEPRECATED))
    async def test_when_test_case_is_not_active_expect_rejection_with_identifier(self, status):
        test_case = _test_case(status)
        repository = AsyncMock(spec=TestCasePersistencePort)
        repository.find_by_id.return_value = test_case
        resolver = TestCaseSnapshotResolver(repository)

        with pytest.raises(EntityNotFoundException, match=str(test_case.identifier)):
            await resolver.resolve("IAG", (test_case.identifier,))

    @pytest.mark.parametrize("status", (VersionStatus.DRAFT, VersionStatus.DEPRECATED))
    async def test_when_test_set_is_not_active_expect_rejection_with_identifier(self, status):
        test_set = _test_set(status)
        repository = AsyncMock(spec=TestSetPersistencePort)
        repository.find_by_id.return_value = test_set
        resolver = TestSetSnapshotResolver(repository)

        with pytest.raises(EntityNotFoundException, match=str(test_set.identifier)):
            await resolver.resolve("IAG", (test_set.identifier,))
