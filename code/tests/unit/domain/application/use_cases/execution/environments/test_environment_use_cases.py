from datetime import UTC, datetime
from uuid import uuid4

import pytest

from test_service.domain.application.commands.execution import (
    ActivateEnvironmentCommand,
    CreateEnvironmentCommand,
    DeactivateEnvironmentCommand,
)
from test_service.domain.application.queries.execution import (
    EnvironmentQuery,
    ListEnvironmentsQuery,
)
from test_service.domain.application.use_cases.execution.environments.activate_environment_use_case import (  # noqa: E501
    ActivateEnvironmentUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.environments.create_environment_use_case import (  # noqa: E501
    CreateEnvironmentUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.environments.deactivate_environment_use_case import (  # noqa: E501
    DeactivateEnvironmentUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.environments.get_environment_use_case import (  # noqa: E501
    GetEnvironmentUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.environments.list_environments_use_case import (  # noqa: E501
    ListEnvironmentsUseCaseImpl,
)
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.environment_already_exists_exception import (
    EnvironmentAlreadyExistsException,
)
from test_service.domain.model.execution.environment import Environment, EnvironmentStatus


def _environment(status: EnvironmentStatus = EnvironmentStatus.ACTIVE) -> Environment:
    return Environment(
        identifier=uuid4(),
        environment_key="staging-eu",
        name="Staging Europe",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        status=status,
    )


class _Repository:
    def __init__(self, environment: Environment | None = None) -> None:
        self.environment = environment
        self.saved: Environment | None = None

    async def save(self, environment: Environment) -> Environment:
        self.saved = environment
        return environment

    async def find_by_id(self, identifier):
        return self.environment

    async def find_by_key(self, environment_key: str):
        return self.environment

    async def find_page(self, pagination):
        return Page((), 0) if self.environment is None else Page((self.environment,), 1)


class TestEnvironmentUseCases:
    async def test_when_creating_new_environment_expect_active_snapshot_saved(self):
        repository = _Repository()
        command = CreateEnvironmentCommand(
            environment_key="staging-eu",
            name="Staging Europe",
            requested_by="author@example.test",
            requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        environment = await CreateEnvironmentUseCaseImpl(repository).execute(command)

        assert environment.status is EnvironmentStatus.ACTIVE
        assert repository.saved == environment

    async def test_when_creating_duplicate_environment_expect_conflict(self):
        environment = _environment()
        command = CreateEnvironmentCommand(
            environment_key=environment.environment_key,
            name=environment.name,
            requested_by="author@example.test",
            requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        use_case = CreateEnvironmentUseCaseImpl(_Repository(environment))

        with pytest.raises(EnvironmentAlreadyExistsException):
            await use_case.execute(command)

    async def test_when_environment_is_missing_expect_not_found(self):
        identifier = uuid4()
        use_case = GetEnvironmentUseCaseImpl(_Repository())
        query = EnvironmentQuery(identifier)

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(query)

    async def test_when_environment_exists_expect_retrieved_snapshot(self):
        environment = _environment()

        result = await GetEnvironmentUseCaseImpl(_Repository(environment)).execute(
            EnvironmentQuery(environment.identifier)
        )

        assert result == environment

    async def test_when_activating_missing_environment_expect_not_found(self):
        identifier = uuid4()
        use_case = ActivateEnvironmentUseCaseImpl(_Repository())
        command = ActivateEnvironmentCommand(identifier)

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(command)

    async def test_when_deactivating_missing_environment_expect_not_found(self):
        identifier = uuid4()
        use_case = DeactivateEnvironmentUseCaseImpl(_Repository())
        command = DeactivateEnvironmentCommand(identifier)

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(command)

    async def test_when_environment_is_activated_expect_saved_active_snapshot(self):
        environment = _environment(EnvironmentStatus.INACTIVE)
        repository = _Repository(environment)

        result = await ActivateEnvironmentUseCaseImpl(repository).execute(
            ActivateEnvironmentCommand(environment.identifier)
        )

        assert result.status is EnvironmentStatus.ACTIVE
        assert repository.saved == result

    async def test_when_environment_is_deactivated_expect_saved_inactive_snapshot(self):
        environment = _environment()
        repository = _Repository(environment)

        result = await DeactivateEnvironmentUseCaseImpl(repository).execute(
            DeactivateEnvironmentCommand(environment.identifier)
        )

        assert result.status is EnvironmentStatus.INACTIVE
        assert repository.saved == result

    async def test_when_environments_are_listed_expect_repository_page(self):
        environment = _environment()
        pagination = PaginationParams(limit=10)

        page = await ListEnvironmentsUseCaseImpl(_Repository(environment)).execute(
            ListEnvironmentsQuery(pagination)
        )

        assert page.items == (environment,)
