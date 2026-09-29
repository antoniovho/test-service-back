"""Mapping between Precondition domain objects and SQLAlchemy DTOs."""

from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.dtos.precondition_dto import (  # noqa: E501
    PreconditionDTO,
)


class PreconditionPersistenceMapper:
    """Translate Precondition data at the domain and persistence boundary."""

    @staticmethod
    def to_domain(precondition: PreconditionDTO) -> Precondition:
        """Create a Precondition aggregate from a persistence DTO."""
        definition = precondition.validation_definition
        return Precondition(
            identifier=precondition.id,
            project_key=precondition.project_key,
            precondition_key=precondition.precondition_key,
            version=precondition.version,
            name=precondition.name,
            description=precondition.description,
            validation_definition=Definition(
                schema_version=str(definition["schema_version"]),
                variables=definition["variables"],
                actions=tuple(
                    Action(
                        identifier=action["identifier"],
                        action_type=action["action_type"],
                        configuration=action["configuration"],
                        source=action.get("source"),
                    )
                    for action in definition["actions"]
                ),
            ),
            status=VersionStatus(precondition.status),
            metadata=precondition.metadata_,
            created_at=precondition.created_at,
            created_by=precondition.created_by,
        )
