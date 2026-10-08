from datetime import UTC, datetime
from uuid import uuid4

from test_service_server.models.create_test_plan_request import CreateTestPlanRequest
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import Page, SortOrder
from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.input.rest.composition.test_plans.test_plan_mapper import (  # noqa: E501
    TestPlanMapper,
)


def _request() -> CreateTestPlanRequest:
    return CreateTestPlanRequest(
        planKey="checkout-nightly",
        name="Checkout nightly",
        description="Nightly regression",
        executionMode="SEQUENTIAL",
        timeoutSeconds=900,
        testSetIds=[uuid4()],
        testCaseIds=[uuid4()],
        exclusions=[uuid4()],
    )


def _snapshot() -> TestPlan:
    return TestPlan(
        uuid4(),
        "IAG",
        "checkout-nightly",
        1,
        "Checkout nightly",
        ExecutionMode.SEQUENTIAL,
        900,
        datetime(2026, 1, 1, tzinfo=UTC),
        "author@example.test",
        test_set_ids=(uuid4(),),
        test_case_ids=(uuid4(),),
        exclusions=(uuid4(),),
        description="Nightly regression",
    )


class TestTestPlanMapper:
    def test_when_request_is_mapped_expect_domain_commands(self):
        request = _request()
        requested_at = datetime(2026, 1, 1, tzinfo=UTC)

        command = TestPlanMapper.to_create_command(
            "IAG", request, "author@example.test", requested_at
        )
        version = TestPlanMapper.to_create_version_command(
            "IAG", uuid4(), request, "author@example.test", requested_at
        )

        assert command.plan_key == request.plan_key
        assert command.execution_mode is ExecutionMode.SEQUENTIAL
        assert command.test_set_ids == tuple(request.test_set_ids)
        assert version.source_id is not None

    def test_when_queries_and_responses_are_mapped_expect_contract_values(self):
        snapshot = _snapshot()
        pagination = TestPlanMapper.to_pagination(0, 10, "createdAt", ApiSortOrder.DESC)

        response = TestPlanMapper.to_list_response(Page((snapshot,), 1), "AI Gateway", pagination)
        versions_response = TestPlanMapper.to_version_list_response(
            Page((snapshot,), 1), "AI Gateway", pagination
        )

        assert pagination.order is SortOrder.DESC
        assert TestPlanMapper.to_pagination(None, None, None, None).limit == 20
        assert TestPlanMapper.to_status("ACTIVE") is VersionStatus.ACTIVE
        assert TestPlanMapper.to_status(None) is None
        assert TestPlanMapper.to_get_query("IAG", snapshot.identifier).project_key == "IAG"
        assert (
            TestPlanMapper.to_activate_command("IAG", snapshot.identifier, "approved").reason
            == "approved"
        )
        assert TestPlanMapper.to_deprecate_command("IAG", snapshot.identifier, None).reason is None
        assert TestPlanMapper.to_list_query("IAG", pagination, None).status is None
        assert (
            TestPlanMapper.to_versions_query("IAG", "checkout-nightly", pagination, None).plan_key
            == "checkout-nightly"
        )
        assert response.data[0].test_case_ids == list(snapshot.test_case_ids)
        assert response.pagination.total == 1
        assert versions_response.data[0].plan_key == snapshot.plan_key
