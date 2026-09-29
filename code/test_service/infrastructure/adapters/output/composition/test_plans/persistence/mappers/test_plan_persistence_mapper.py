"""Mapping between Test Plan domain snapshots and persistence DTOs."""

from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.dtos.test_plan_dto import (  # noqa: E501
    TestPlanDTO,
    TestPlanExclusionDTO,
    TestPlanTestCaseDTO,
    TestPlanTestSetDTO,
)


class TestPlanPersistenceMapper:
    """Translate immutable Test Plan snapshots to SQLAlchemy DTOs and back."""

    @staticmethod
    def to_dto(snapshot: TestPlan) -> TestPlanDTO:
        """Map one domain snapshot and its immutable references to persistence."""
        return TestPlanDTO(
            id=snapshot.identifier,
            project_key=snapshot.project_key,
            plan_key=snapshot.plan_key,
            version=snapshot.version,
            name=snapshot.name,
            description=snapshot.description,
            status=snapshot.status.value,
            execution_mode=snapshot.execution_mode.value,
            max_parallelism=snapshot.max_parallelism,
            timeout_seconds=snapshot.timeout_seconds,
            created_at=snapshot.created_at,
            created_by=snapshot.created_by,
            test_set_links=[
                TestPlanTestSetDTO(test_set_id=identifier) for identifier in snapshot.test_set_ids
            ],
            test_case_links=[
                TestPlanTestCaseDTO(test_case_id=identifier)
                for identifier in snapshot.test_case_ids
            ],
            exclusion_links=[
                TestPlanExclusionDTO(test_case_id=identifier) for identifier in snapshot.exclusions
            ],
        )

    @staticmethod
    def to_domain(dto: TestPlanDTO) -> TestPlan:
        """Map one fully-loaded persistence DTO to a domain snapshot."""
        return TestPlan(
            identifier=dto.id,
            project_key=dto.project_key,
            plan_key=dto.plan_key,
            version=dto.version,
            name=dto.name,
            description=dto.description,
            status=VersionStatus(dto.status),
            execution_mode=ExecutionMode(dto.execution_mode),
            max_parallelism=dto.max_parallelism,
            timeout_seconds=dto.timeout_seconds,
            created_at=dto.created_at,
            created_by=dto.created_by,
            test_set_ids=tuple(link.test_set_id for link in dto.test_set_links),
            test_case_ids=tuple(link.test_case_id for link in dto.test_case_links),
            exclusions=tuple(link.test_case_id for link in dto.exclusion_links),
        )
