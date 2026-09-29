from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
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


class TestPreconditionMapper:
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
