from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from test_service.domain.application.services.precondition_reference_resolver import (
    PreconditionReferenceResolver,
)
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.exceptions.entity_not_found_exception import (
    EntityNotFoundException,
)
from test_service.domain.model.exceptions.precondition_project_mismatch_exception import (
    PreconditionProjectMismatchException,
)


class InMemoryPreconditionRepository:
    def __init__(self, preconditions: tuple[Precondition, ...]) -> None:
        self._preconditions = {
            precondition.identifier: precondition for precondition in preconditions
        }

    async def find_by_id(self, identifier: UUID) -> Precondition | None:
        return self._preconditions.get(identifier)


def _precondition(**overrides: object) -> Precondition:
    fields = {
        "identifier": uuid4(),
        "project_key": "IAG",
        "precondition_key": "customer-is-authenticated",
        "version": 2,
        "name": "Customer is authenticated",
        "description": "Customer has a valid session",
        "validation_definition": Definition(
            variables={},
            actions=(Action(identifier="validate", action_type="HTTP_REQUEST", configuration={}),),
        ),
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": "user@example.com",
    }
    fields.update(overrides)
    return Precondition(**fields)


class TestPreconditionReferenceResolver:
    async def test_when_snapshots_belong_to_project_expect_immutable_references(self):
        precondition = _precondition()
        resolver = PreconditionReferenceResolver(InMemoryPreconditionRepository((precondition,)))

        references = await resolver.resolve("IAG", (precondition.identifier,))

        assert len(references) == 1
        assert references[0].identifier == precondition.identifier
        assert references[0].precondition_key == precondition.precondition_key
        assert references[0].version == precondition.version

    async def test_when_snapshot_does_not_exist_expect_not_found_exception(self):
        identifier = uuid4()
        resolver = PreconditionReferenceResolver(InMemoryPreconditionRepository(()))

        with pytest.raises(EntityNotFoundException) as exception:
            await resolver.resolve("IAG", (identifier,))

        assert exception.value.code == "ENTITY_NOT_FOUND"

    async def test_when_snapshot_belongs_to_another_project_expect_mismatch_exception(self):
        precondition = _precondition(project_key="OTHER")
        resolver = PreconditionReferenceResolver(InMemoryPreconditionRepository((precondition,)))

        with pytest.raises(PreconditionProjectMismatchException) as exception:
            await resolver.resolve("IAG", (precondition.identifier,))

        assert exception.value.code == "PRECONDITION_PROJECT_MISMATCH"
