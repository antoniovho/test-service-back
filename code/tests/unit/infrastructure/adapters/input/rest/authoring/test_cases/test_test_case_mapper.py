from datetime import UTC, datetime
from uuid import uuid4

from test_service_server.models.action import Action as ApiAction
from test_service_server.models.create_test_case_request import CreateTestCaseRequest
from test_service_server.models.definition import Definition as ApiDefinition
from test_service_server.models.precondition_version_reference import PreconditionVersionReference
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import SortOrder
from test_service.domain.model.authoring.test_case import Priority, TestLevel, TestType
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.input.rest.authoring.test_cases.test_case_mapper import (  # noqa: E501
    TestCaseMapper,
)


def _request() -> CreateTestCaseRequest:
    return CreateTestCaseRequest(
        testKey="IAG-1",
        name="Gateway test",
        summary="Checks the gateway",
        objective="Receive success",
        testType="AUTOMATED",
        testLevel="FUNCTIONAL",
        priority="HIGH",
        timeoutSeconds=30,
        metadata={"team": "gateway"},
        preconditions=[PreconditionVersionReference(id=uuid4())],
        definition=ApiDefinition(
            schemaVersion="1.0",
            variables={"url": "https://example.test"},
            actions=[ApiAction(id="request", type="HTTP_REQUEST", source="http", config={})],
        ),
    )


class TestTestCaseMapper:
    def test_when_create_commands_are_mapped_expect_domain_values(self):
        request = _request()
        requested_at = datetime(2026, 1, 1, tzinfo=UTC)
        source_id = uuid4()

        create = TestCaseMapper.to_create_command(
            "IAG", request, "author@example.test", requested_at
        )
        version = TestCaseMapper.to_create_version_command(
            "IAG", source_id, request, "author@example.test", requested_at
        )

        assert create.test_key == "IAG-1"
        assert create.test_type is TestType.AUTOMATED
        assert create.test_level is TestLevel.FUNCTIONAL
        assert create.priority is Priority.HIGH
        assert create.preconditions == (request.preconditions[0].id,)
        assert version.source_id == source_id

    def test_when_queries_and_filters_are_mapped_expect_domain_primitives(self):
        identifier = uuid4()
        pagination = TestCaseMapper.to_pagination(3, 10, "createdAt", ApiSortOrder.DESC)

        assert pagination.offset == 3
        assert pagination.sort_by == "created_at"
        assert pagination.order is SortOrder.DESC
        assert TestCaseMapper.to_pagination(None, None, None, None).limit == 20
        assert TestCaseMapper.to_status("ACTIVE") is VersionStatus.ACTIVE
        assert TestCaseMapper.to_status(None) is None
        assert TestCaseMapper.to_get_query(identifier).identifier == identifier
        assert TestCaseMapper.to_activate_command(identifier, "ok").reason == "ok"
        assert TestCaseMapper.to_deprecate_command(identifier, None).reason is None
        assert TestCaseMapper.to_list_query("IAG", pagination, None).project_key == "IAG"
        assert (
            TestCaseMapper.to_versions_query("IAG", "IAG-1", pagination, None).test_key == "IAG-1"
        )
