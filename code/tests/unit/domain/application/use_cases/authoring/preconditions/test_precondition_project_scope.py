from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from test_service.domain.application.commands.authoring import (
    ActivatePreconditionCommand,
    DeprecatePreconditionCommand,
)
from test_service.domain.application.queries.authoring import PreconditionQuery
from test_service.domain.application.use_cases.authoring.preconditions.activate_precondition_use_case import (  # noqa: E501
    ActivatePreconditionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.deprecate_precondition_use_case import (  # noqa: E501
    DeprecatePreconditionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.get_precondition_use_case import (  # noqa: E501
    GetPreconditionUseCaseImpl,
)
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.exceptions.entity_not_found_exception import (
    EntityNotFoundException,
)
from test_service.domain.model.lifecycle import VersionStatus


class _Repository:
    def __init__(self, precondition: Precondition) -> None:
        self._precondition = precondition
        self.saved: Precondition | None = None

    async def find_by_id(self, identifier: UUID) -> Precondition | None:
        return self._precondition if identifier == self._precondition.identifier else None

    async def save(self, snapshot: Precondition) -> Precondition:
        self.saved = snapshot
        return snapshot

    async def find_latest_version(self, project_key: str, precondition_key: str) -> int | None:
        return None

    async def find_page(
        self,
        project_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[Precondition]:
        return Page((), total=0)

    async def find_versions(
        self,
        project_key: str,
        precondition_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[Precondition]:
        return Page((), total=0)


def _precondition(status: VersionStatus = VersionStatus.DRAFT) -> Precondition:
    return Precondition(
        identifier=uuid4(),
        project_key="OTHER",
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
        status=status,
    )


class TestPreconditionProjectScope:
    async def test_when_precondition_belongs_to_another_project_expect_not_found_exception(self):
        precondition = _precondition()
        use_case = GetPreconditionUseCaseImpl(_Repository(precondition))
        request = PreconditionQuery("IAG", precondition.identifier)

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(request)

    @pytest.mark.parametrize(
        ("use_case_class", "command_class", "status"),
        [
            (ActivatePreconditionUseCaseImpl, ActivatePreconditionCommand, VersionStatus.DRAFT),
            (DeprecatePreconditionUseCaseImpl, DeprecatePreconditionCommand, VersionStatus.ACTIVE),
        ],
        ids=["activate", "deprecate"],
    )
    async def test_when_lifecycle_precondition_belongs_to_another_project_expect_not_found_exception(  # noqa: E501
        self, use_case_class, command_class, status
    ):
        precondition = _precondition(status)
        repository = _Repository(precondition)
        use_case = use_case_class(repository)
        request = command_class("IAG", precondition.identifier)

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(request)

        assert repository.saved is None
