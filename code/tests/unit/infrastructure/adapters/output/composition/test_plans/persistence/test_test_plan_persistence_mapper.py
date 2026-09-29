from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.mappers.test_plan_persistence_mapper import (  # noqa: E501
    TestPlanPersistenceMapper,
)


class TestTestPlanPersistenceMapper:
    def test_when_test_plan_is_mapped_expect_persistence_references_round_trip(self):
        test_set_id, test_case_id, exclusion_id = uuid4(), uuid4(), uuid4()
        test_plan = TestPlan(
            uuid4(),
            "IAG",
            "checkout-nightly",
            2,
            "Checkout nightly",
            ExecutionMode.PARALLEL,
            900,
            datetime(2026, 1, 1, tzinfo=UTC),
            "author@example.test",
            (test_set_id,),
            (test_case_id,),
            (exclusion_id,),
            "Regression",
            4,
            VersionStatus.ACTIVE,
        )

        dto = TestPlanPersistenceMapper.to_dto(test_plan)
        result = TestPlanPersistenceMapper.to_domain(dto)

        assert dto.status == "ACTIVE"
        assert dto.test_set_links[0].test_set_id == test_set_id
        assert dto.test_case_links[0].test_case_id == test_case_id
        assert dto.exclusion_links[0].test_case_id == exclusion_id
        assert result == test_plan
