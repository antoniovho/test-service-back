from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.dtos.precondition_dto import (  # noqa: E501
    PreconditionDTO,
)
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.mappers.precondition_persistence_mapper import (  # noqa: E501
    PreconditionPersistenceMapper,
)


class TestPreconditionPersistenceMapper:
    def test_when_dto_is_mapped_expect_domain_precondition(self):
        dto = PreconditionDTO(
            id=uuid4(),
            project_key="IAG",
            precondition_key="authenticated",
            version=2,
            name="Authenticated user",
            description="An authenticated user is available",
            validation_definition={
                "schema_version": "1.0",
                "variables": {"user": "test"},
                "actions": [
                    {
                        "identifier": "session",
                        "action_type": "CHECK_SESSION",
                        "configuration": {"required": True},
                    }
                ],
            },
            status="ACTIVE",
            metadata_={"team": "identity"},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="author@example.test",
        )

        result = PreconditionPersistenceMapper.to_domain(dto)

        assert result.identifier == dto.id
        assert result.status is VersionStatus.ACTIVE
        assert result.validation_definition.actions[0].source is None
        assert result.metadata == dto.metadata_
