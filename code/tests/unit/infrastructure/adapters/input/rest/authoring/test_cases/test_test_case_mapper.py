from datetime import UTC, datetime
from uuid import uuid4

from test_service_server.models.action import Action as ApiAction
from test_service_server.models.create_test_case_request import CreateTestCaseRequest
from test_service_server.models.definition import Definition as ApiDefinition
from test_service_server.models.precondition_version_reference import PreconditionVersionReference
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import (
    Priority,
    TestCase,
    TestLevel,
    TestType,
)
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


def _test_case() -> TestCase:
    return TestCase(
        identifier=uuid4(),
        project_key="IAG",
        test_key="IAG-1",
        version=1,
        name="Gateway test",
        summary="Checks the gateway",
        objective="Receive success",
        test_type=TestType.AUTOMATED,
        test_level=TestLevel.FUNCTIONAL,
        priority=Priority.HIGH,
        definition=Definition(
            schema_version="1.0",
            variables={},
            actions=(Action(identifier="request", action_type="HTTP_REQUEST", configuration={}),),
        ),
        timeout_seconds=30,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        metadata={"team": "gateway"},
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
        assert TestCaseMapper.to_get_query("IAG", identifier).project_key == "IAG"
        assert TestCaseMapper.to_activate_command("IAG", identifier, "ok").reason == "ok"
        assert TestCaseMapper.to_deprecate_command("IAG", identifier, None).reason is None
        assert TestCaseMapper.to_list_query("IAG", pagination, None).project_key == "IAG"
        assert (
            TestCaseMapper.to_versions_query("IAG", "IAG-1", pagination, None).test_key == "IAG-1"
        )

    def test_when_test_case_is_mapped_expect_api_resource(self):
        test_case = _test_case()

        response = TestCaseMapper.to_api(test_case, "AI Gateway")

        assert response.id == test_case.identifier
        assert response.project.name == "AI Gateway"
        assert response.definition.actions[0].id == "request"
        assert response.metadata == {"team": "gateway"}

    def test_when_test_case_page_is_mapped_expect_typed_list_responses(self):
        test_case = _test_case()
        page = Page((test_case,), total=1)
        pagination = PaginationParams(offset=0, limit=10)

        list_response = TestCaseMapper.to_list_response(page, "AI Gateway", pagination)
        version_response = TestCaseMapper.to_version_list_response(page, "AI Gateway", pagination)

        assert list_response.pagination.total == 1
        assert list_response.data[0].test_key == "IAG-1"
        assert version_response.pagination.limit == 10
        assert version_response.data[0].id == test_case.identifier
