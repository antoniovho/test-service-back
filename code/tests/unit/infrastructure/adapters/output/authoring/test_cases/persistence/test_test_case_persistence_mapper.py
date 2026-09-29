from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import (
    PreconditionReference,
    Priority,
    TestCase,
    TestLevel,
    TestType,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.dtos.precondition_dto import (  # noqa: E501
    PreconditionDTO,
)
from test_service.infrastructure.adapters.output.authoring.test_cases.persistence.mappers.test_case_persistence_mapper import (  # noqa: E501
    TestCasePersistenceMapper,
)


def _test_case() -> TestCase:
    return TestCase(
        identifier=uuid4(),
        project_key="IAG",
        test_key="IAG-1",
        version=2,
        name="Gateway test",
        summary="Checks the gateway",
        objective="Receive a success response",
        test_type=TestType.AUTOMATED,
        test_level=TestLevel.FUNCTIONAL,
        priority=Priority.HIGH,
        definition=Definition(
            schema_version="1.0",
            variables={"url": "https://example.test"},
            actions=(
                Action(
                    identifier="request",
                    action_type="HTTP_REQUEST",
                    configuration={"method": "GET"},
                    source="http",
                ),
            ),
        ),
        timeout_seconds=30,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        preconditions=(PreconditionReference(uuid4(), "authenticated", 3),),
        status=VersionStatus.ACTIVE,
        metadata={"team": "gateway"},
    )


class TestTestCasePersistenceMapper:
    def test_when_test_case_is_mapped_expect_dto_fields_and_ordered_links(self):
        test_case = _test_case()

        dto = TestCasePersistenceMapper.to_dto(test_case)

        assert dto.id == test_case.identifier
        assert dto.status == "ACTIVE"
        assert dto.definition["actions"][0]["source"] == "http"
        assert dto.precondition_links[0].precondition_id == test_case.preconditions[0].identifier
        assert dto.precondition_links[0].position == 0

    def test_when_fully_loaded_dto_is_mapped_expect_domain_round_trip(self):
        test_case = _test_case()
        dto = TestCasePersistenceMapper.to_dto(test_case)
        dto.precondition_links[0].precondition = PreconditionDTO(
            id=test_case.preconditions[0].identifier,
            project_key=test_case.project_key,
            precondition_key=test_case.preconditions[0].precondition_key,
            version=test_case.preconditions[0].version,
            name="Authenticated",
            description="An authenticated user is available",
            validation_definition={"schema_version": "1.0", "variables": {}, "actions": []},
            status="ACTIVE",
            metadata_={},
            created_at=test_case.created_at,
            created_by=test_case.created_by,
        )

        result = TestCasePersistenceMapper.to_domain(dto)

        assert result == test_case
