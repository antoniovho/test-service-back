from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from test_service_server.models.action import Action as ApiAction
from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_precondition_request import CreatePreconditionRequest
from test_service_server.models.definition import Definition as ApiDefinition
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import Page
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.ports.input.use_cases.authoring.preconditions.activate_precondition_use_case import (  # noqa: E501
    ActivatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.create_precondition_use_case import (  # noqa: E501
    CreatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.create_precondition_version_use_case import (  # noqa: E501
    CreatePreconditionVersionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.deprecate_precondition_use_case import (  # noqa: E501
    DeprecatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.get_precondition_use_case import (  # noqa: E501
    GetPreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.list_precondition_versions_use_case import (  # noqa: E501
    ListPreconditionVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.list_preconditions_use_case import (  # noqa: E501
    ListPreconditionsUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.infrastructure.adapters.input.rest.authoring.preconditions.preconditions_rest_controller import (  # noqa: E501
    PreconditionsRestController,
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
        metadata={},
    )


def _request() -> CreatePreconditionRequest:
    return CreatePreconditionRequest(
        preconditionKey="authenticated",
        name="Authenticated user",
        description="User has a valid session",
        validationDefinition=ApiDefinition(
            schemaVersion="1.0",
            variables={},
            actions=[ApiAction(id="session", type="CHECK_SESSION", config={})],
        ),
    )


def _controller(precondition: Precondition) -> PreconditionsRestController:
    controller = PreconditionsRestController.__new__(PreconditionsRestController)
    controller.__dict__.update(
        _create=SimpleNamespace(execute=AsyncMock(return_value=precondition)),
        _create_version=SimpleNamespace(execute=AsyncMock(return_value=precondition)),
        _get=SimpleNamespace(execute=AsyncMock(return_value=precondition)),
        _activate=SimpleNamespace(execute=AsyncMock(return_value=precondition)),
        _deprecate=SimpleNamespace(execute=AsyncMock(return_value=precondition)),
        _list=SimpleNamespace(execute=AsyncMock(return_value=Page((precondition,), 1))),
        _list_versions=SimpleNamespace(execute=AsyncMock(return_value=Page((precondition,), 1))),
        _get_project=SimpleNamespace(
            execute=AsyncMock(return_value=SimpleNamespace(name="AI Gateway"))
        ),
    )
    return controller


class TestPreconditionsRestController:
    def test_when_constructed_expect_all_required_use_cases_injected(self, monkeypatch):
        injector = SimpleNamespace(inject=MagicMock(side_effect=range(8)))
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.authoring.preconditions."
            "preconditions_rest_controller.get_injector",
            lambda: injector,
        )

        controller = PreconditionsRestController()

        assert controller._create == 0
        assert controller._get_project == 7
        assert injector.inject.call_args_list == [
            ((CreatePreconditionUseCase,),),
            ((CreatePreconditionVersionUseCase,),),
            ((GetPreconditionUseCase,),),
            ((ActivatePreconditionUseCase,),),
            ((DeprecatePreconditionUseCase,),),
            ((ListPreconditionsUseCase,),),
            ((ListPreconditionVersionsUseCase,),),
            ((GetProjectUseCase,),),
        ]

    async def test_when_precondition_commands_are_requested_expect_api_preconditions(
        self, monkeypatch
    ):
        precondition = _precondition()
        controller = _controller(precondition)
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.authoring.preconditions."
            "preconditions_rest_controller.get_current_identity",
            lambda: "author@example.test",
        )

        created = await controller.create("IAG", _request())
        found = await controller.get("IAG", precondition.identifier)
        version = await controller.create_version("IAG", precondition.identifier, _request())
        activated = await controller.activate(
            "IAG", precondition.identifier, ActionRequest(reason="approved")
        )
        deprecated = await controller.deprecate("IAG", precondition.identifier, None)

        assert created.id == precondition.identifier
        assert found.project.name == "AI Gateway"
        assert version.precondition_key == precondition.precondition_key
        assert activated.status == "DRAFT"
        assert deprecated.validation_definition.actions[0].id == "session"

    async def test_when_preconditions_are_listed_expect_api_pagination(self):
        precondition = _precondition()
        controller = _controller(precondition)

        listed = await controller.list("IAG", "DRAFT", 0, 10, "version", ApiSortOrder.ASC)
        versions = await controller.list_versions(
            "IAG", "authenticated", None, None, None, "createdAt", ApiSortOrder.DESC
        )

        assert listed.pagination.total == 1
        assert listed.data[0].id == precondition.identifier
        assert versions.pagination.offset == 0
        assert versions.data[0].precondition_key == "authenticated"
