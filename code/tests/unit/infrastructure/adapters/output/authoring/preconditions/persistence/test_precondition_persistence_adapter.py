from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.model.authoring.precondition import Precondition
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.dtos.precondition_dto import (  # noqa: E501
    PreconditionDTO,
)
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.precondition_persistence_adapter import (  # noqa: E501
    PreconditionPersistenceAdapter,
)


def _dto() -> PreconditionDTO:
    return PreconditionDTO(
        id=uuid4(),
        project_key="IAG",
        precondition_key="authenticated",
        version=1,
        name="Authenticated user",
        description="User has a session",
        validation_definition={
            "schema_version": "1.0",
            "variables": {},
            "actions": [
                {
                    "identifier": "session",
                    "action_type": "CHECK_SESSION",
                    "configuration": {},
                }
            ],
        },
        status="DRAFT",
        metadata_={},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
    )


class _Repository:
    def __init__(self, dto: PreconditionDTO | None) -> None:
        self.dto = dto

    async def find_by_id(self, _):
        return self.dto


class TestPreconditionPersistenceAdapter:
    async def test_when_precondition_exists_expect_domain_precondition(self):
        dto = _dto()

        result = await PreconditionPersistenceAdapter(_Repository(dto)).find_by_id(dto.id)

        assert isinstance(result, Precondition)
        assert result.identifier == dto.id

    async def test_when_precondition_is_absent_expect_none(self):
        result = await PreconditionPersistenceAdapter(_Repository(None)).find_by_id(uuid4())

        assert result is None
