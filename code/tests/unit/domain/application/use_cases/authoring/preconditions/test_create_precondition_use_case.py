from datetime import UTC, datetime
from uuid import UUID

import pytest

from test_service.domain.application.commands.authoring import CreatePreconditionCommand
from test_service.domain.application.use_cases.authoring.preconditions.create_precondition_use_case import (  # noqa: E501
    CreatePreconditionUseCaseImpl,
)
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.exceptions.precondition_already_exists_exception import (  # noqa: E501
    PreconditionAlreadyExistsException,
)


def _definition() -> Definition:
    return Definition(
        schema_version="1.0",
        variables={},
        actions=(Action(identifier="session", action_type="CHECK_SESSION", configuration={}),),
    )


def _command() -> CreatePreconditionCommand:
    return CreatePreconditionCommand(
        project_key="IAG",
        precondition_key="authenticated",
        name="Authenticated user",
        description="User has a valid session",
        validation_definition=_definition(),
        requested_by="author@example.test",
        requested_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class _Repository:
    def __init__(self, latest_version: int | None) -> None:
        self._latest_version = latest_version
        self.saved: Precondition | None = None

    async def find_latest_version(self, _project_key: str, _precondition_key: str) -> int | None:
        return self._latest_version

    async def save(self, precondition: Precondition) -> Precondition:
        self.saved = precondition
        return precondition

    async def find_by_id(self, _identifier: UUID) -> Precondition | None:
        return None


class TestCreatePreconditionUseCaseImpl:
    async def test_when_precondition_key_is_new_expect_first_draft_persisted(self):
        repository = _Repository(None)
        use_case = CreatePreconditionUseCaseImpl(repository)

        precondition = await use_case.execute(_command())

        assert precondition.version == 1
        assert repository.saved == precondition

    async def test_when_precondition_key_exists_expect_conflict_with_version_endpoint(self):
        use_case = CreatePreconditionUseCaseImpl(_Repository(1))
        request = _command()

        with pytest.raises(PreconditionAlreadyExistsException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "PRECONDITION_ALREADY_EXISTS"
        assert (
            "/v1/projects/IAG/preconditions/{preconditionId}/versions"
            in exception.value.error_description
        )
