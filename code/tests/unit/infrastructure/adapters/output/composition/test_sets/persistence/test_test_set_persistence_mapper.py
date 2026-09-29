from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.composition.test_sets.persistence.mappers.test_set_persistence_mapper import (  # noqa: E501
    TestSetPersistenceMapper,
)


class TestTestSetPersistenceMapper:
    def test_when_test_set_is_mapped_expect_ordered_persistence_links(self):
        first, second = uuid4(), uuid4()
        test_set = TestSet(
            uuid4(),
            "IAG",
            "checkout",
            2,
            "Checkout",
            (first, second),
            datetime(2026, 1, 1, tzinfo=UTC),
            "author@example.test",
            "Regression",
            VersionStatus.ACTIVE,
        )

        dto = TestSetPersistenceMapper.to_dto(test_set)
        result = TestSetPersistenceMapper.to_domain(dto)

        assert dto.status == "ACTIVE"
        assert [item.position for item in dto.item_links] == [0, 1]
        assert result == test_set
