"""Validation of Test Set snapshots referenced by Test Plan composition."""

from collections.abc import Iterable
from uuid import UUID

from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)


class TestSetSnapshotResolver:
    """Resolve Test Set UUIDs while enforcing their project ownership."""

    def __init__(self, test_set_repository: TestSetPersistencePort) -> None:
        self._test_set_repository = test_set_repository

    async def resolve(self, project_key: str, identifiers: Iterable[UUID]) -> tuple[UUID, ...]:
        """Return validated immutable Test Set snapshot identifiers."""
        snapshots: list[UUID] = []
        for identifier in identifiers:
            test_set = await self._test_set_repository.find_by_id(identifier)
            if (
                test_set is None
                or test_set.project_key != project_key
                or test_set.status is not VersionStatus.ACTIVE
            ):
                raise EntityNotFoundException(
                    "Test set", str(identifier), f"active snapshots in project '{project_key}'"
                )
            snapshots.append(test_set.identifier)
        return tuple(snapshots)
