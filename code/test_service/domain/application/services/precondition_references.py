"""Resolution of precondition UUIDs into immutable domain references."""

from collections.abc import Iterable
from uuid import UUID

from test_service.domain.model.authoring.test_case import PreconditionReference
from test_service.domain.model.exceptions.entity_not_found_exception import (
    EntityNotFoundException,
)
from test_service.domain.model.exceptions.precondition_project_mismatch_exception import (
    PreconditionProjectMismatchException,
)
from test_service.domain.ports.output.repositories import PreconditionRepositoryPort


class PreconditionReferenceResolver:
    """Resolve request UUIDs while enforcing their project ownership."""

    def __init__(self, precondition_repository: PreconditionRepositoryPort) -> None:
        self._precondition_repository = precondition_repository

    async def resolve(
        self, project_key: str, identifiers: Iterable[UUID]
    ) -> tuple[PreconditionReference, ...]:
        """Return immutable references for the requested precondition snapshots.

        Raises:
            EntityNotFoundException: If a referenced snapshot does not exist.
            PreconditionProjectMismatchException: If a snapshot belongs to another project.
        """
        references: list[PreconditionReference] = []
        for identifier in identifiers:
            precondition = await self._precondition_repository.find_by_id(identifier)
            if precondition is None:
                raise EntityNotFoundException("precondition", str(identifier))
            if precondition.project_key != project_key:
                raise PreconditionProjectMismatchException(
                    "precondition snapshot does not belong to the test case project"
                )
            references.append(
                PreconditionReference(
                    identifier=precondition.identifier,
                    precondition_key=precondition.precondition_key,
                    version=precondition.version,
                )
            )
        return tuple(references)
