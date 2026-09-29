from datetime import UTC, datetime
from uuid import uuid4

from test_service_server.models.action import Action as ApiAction
from test_service_server.models.create_precondition_request import CreatePreconditionRequest
from test_service_server.models.definition import Definition as ApiDefinition
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.input.rest.authoring.preconditions.precondition_mapper import (  # noqa: E501
    PreconditionMapper,
)


def _precondition() -> Precondition:
    return Precondition(
        identifier=uuid4(),
        project_key="IAG",
        precondition_key="authenticated",
        version=1,
        name="Authenticated user",
        description="User has a valid session",
        validation_definition=Definition(
            schema_version="1.0",
            variables={},
            actions=(Action(identifier="session", action_type="CHECK_SESSION", configuration={}),),
        ),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        metadata={"team": "gateway"},
    )


def _request() -> CreatePreconditionRequest:
    return CreatePreconditionRequest(
        preconditionKey="authenticated",
        name="Authenticated user",
        description="User has a valid session",
        metadata={"team": "gateway"},
        validationDefinition=ApiDefinition(
            schemaVersion="1.0",
            variables={"tenant": "iag"},
            actions=[ApiAction(id="session", type="CHECK_SESSION", source="identity", config={})],
        ),
    )


class TestPreconditionMapper:
    def test_when_create_commands_are_mapped_expect_domain_values(self):
        request = _request()
        requested_at = datetime(2026, 1, 1, tzinfo=UTC)
        source_id = uuid4()

        create = PreconditionMapper.to_create_command(
            "IAG", request, "author@example.test", requested_at
        )
        version = PreconditionMapper.to_create_version_command(
            "IAG", source_id, request, "author@example.test", requested_at
        )

        assert create.precondition_key == "authenticated"
        assert create.validation_definition.actions[0].source == "identity"
        assert version.source_id == source_id
        assert version.metadata == {"team": "gateway"}

    def test_when_queries_and_filters_are_mapped_expect_domain_primitives(self):
        pagination = PreconditionMapper.to_pagination(3, 10, "createdAt", ApiSortOrder.DESC)

        assert pagination.offset == 3
        assert pagination.sort_by == "created_at"
        assert pagination.order is SortOrder.DESC
        assert PreconditionMapper.to_pagination(None, None, None, None).limit == 20
        assert PreconditionMapper.to_status("ACTIVE") is VersionStatus.ACTIVE
        assert PreconditionMapper.to_status(None) is None
        assert PreconditionMapper.to_list_query("IAG", pagination, None).project_key == "IAG"
        assert (
            PreconditionMapper.to_versions_query(
                "IAG", "authenticated", pagination, None
            ).precondition_key
            == "authenticated"
        )

    def test_when_project_scoped_operations_are_mapped_expect_project_key_preserved(self):
        identifier = uuid4()

        get_query = PreconditionMapper.to_get_query("IAG", identifier)
        activate_command = PreconditionMapper.to_activate_command("IAG", identifier, "approved")
        deprecate_command = PreconditionMapper.to_deprecate_command("IAG", identifier, None)

        assert get_query.project_key == "IAG"
        assert activate_command.project_key == "IAG"
        assert activate_command.reason == "approved"
        assert deprecate_command.project_key == "IAG"

    def test_when_precondition_is_mapped_expect_api_resource(self):
        precondition = _precondition()

        response = PreconditionMapper.to_api(precondition, "AI Gateway")

        assert response.id == precondition.identifier
        assert response.project.name == "AI Gateway"
        assert response.validation_definition.actions[0].id == "session"
        assert response.metadata == {"team": "gateway"}

    def test_when_precondition_page_is_mapped_expect_api_list_response(self):
        precondition = _precondition()
        page = Page((precondition,), total=1)
        pagination = PaginationParams(offset=0, limit=10)

        response = PreconditionMapper.to_list_response(page, "AI Gateway", pagination)

        assert response.pagination.total == 1
        assert response.pagination.limit == 10
        assert response.data[0].precondition_key == "authenticated"
