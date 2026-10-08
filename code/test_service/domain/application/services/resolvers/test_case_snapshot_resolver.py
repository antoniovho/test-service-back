"""Validation of Test Case snapshots referenced by Test Set composition."""

from collections.abc import Iterable
from uuid import UUID

from test_service.domain.model.exceptions.entity_not_found_exception import (
    EntityNotFoundException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)


class TestCaseSnapshotResolver:
    """Resolve Test Case UUIDs while enforcing their project ownership."""

    def __init__(self, test_case_repository: TestCasePersistencePort) -> None:
        self._test_case_repository = test_case_repository

    async def resolve(self, project_key: str, identifiers: Iterable[UUID]) -> tuple[UUID, ...]:
        """Return validated immutable Test Case snapshot identifiers."""
        snapshots: list[UUID] = []
        for identifier in identifiers:
            test_case = await self._test_case_repository.find_by_id(identifier)
            if (
                test_case is None
                or test_case.project_key != project_key
                or test_case.status is not VersionStatus.ACTIVE
            ):
                raise EntityNotFoundException(
                    "Test case", str(identifier), f"active snapshots in project '{project_key}'"
                )
            snapshots.append(test_case.identifier)
        return tuple(snapshots)
