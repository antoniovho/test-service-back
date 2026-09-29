from datetime import UTC, datetime
from uuid import uuid4

from test_service_server.models.create_test_set_request import CreateTestSetRequest
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import Page, SortOrder
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.input.rest.composition.test_sets.test_set_mapper import (
    TestSetMapper,
)


def _snapshot() -> TestSet:
    return TestSet(
        uuid4(),
        "IAG",
        "checkout",
        1,
        "Checkout",
        (uuid4(),),
        datetime(2026, 1, 1, tzinfo=UTC),
        "author@example.test",
    )


class TestTestSetMapper:
    def test_when_request_is_mapped_expect_domain_command(self):
        request = CreateTestSetRequest(setKey="checkout", name="Checkout", items=[uuid4()])

        command = TestSetMapper.to_create_command(
            "IAG", request, "author@example.test", datetime(2026, 1, 1, tzinfo=UTC)
        )

        assert command.project_key == "IAG"
        assert command.items == tuple(request.items)

    def test_when_queries_and_responses_are_mapped_expect_contract_values(self):
        snapshot = _snapshot()
        pagination = TestSetMapper.to_pagination(0, 10, "createdAt", ApiSortOrder.DESC)

        response = TestSetMapper.to_list_response(Page((snapshot,), 1), "AI Gateway", pagination)

        assert pagination.order is SortOrder.DESC
        assert TestSetMapper.to_status("ACTIVE") is VersionStatus.ACTIVE
        assert TestSetMapper.to_get_query("IAG", snapshot.identifier).project_key == "IAG"
        assert response.data[0].items == list(snapshot.items)
        assert response.pagination.total == 1
