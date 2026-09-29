"""Mapping between Test Set domain snapshots and persistence DTOs."""

from uuid import uuid4

from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.composition.test_sets.persistence.dtos.test_set_dto import (  # noqa: E501
    TestSetDTO,
    TestSetItemDTO,
)


class TestSetPersistenceMapper:
    """Translate Test Set aggregate snapshots to and from SQLAlchemy DTOs."""

    @staticmethod
    def to_dto(test_set: TestSet) -> TestSetDTO:
        """Return a persistence DTO retaining the ordered Test Case references."""
        return TestSetDTO(
            id=test_set.identifier,
            project_key=test_set.project_key,
            set_key=test_set.set_key,
            version=test_set.version,
            name=test_set.name,
            description=test_set.description,
            status=test_set.status.value,
            created_at=test_set.created_at,
            created_by=test_set.created_by,
            item_links=[
                TestSetItemDTO(id=uuid4(), test_case_id=item, position=position)
                for position, item in enumerate(test_set.items)
            ],
        )

    @staticmethod
    def to_domain(dto: TestSetDTO) -> TestSet:
        """Return a domain snapshot preserving the persisted item order."""
        return TestSet(
            identifier=dto.id,
            project_key=dto.project_key,
            set_key=dto.set_key,
            version=dto.version,
            name=dto.name,
            description=dto.description,
            status=VersionStatus(dto.status),
            items=tuple(item.test_case_id for item in dto.item_links),
            created_at=dto.created_at,
            created_by=dto.created_by,
        )
