"""Use case implementation: list environments."""

from test_service.domain.application.queries.execution import ListEnvironmentsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.environment import Environment
from test_service.domain.ports.input.use_cases.execution.environments.list_environments_use_case import (  # noqa: E501
    ListEnvironmentsUseCase,
)
from test_service.domain.ports.output.persistence.environments.environment_persistence_port import (  # noqa: E501
    EnvironmentPersistencePort,
)


class ListEnvironmentsUseCaseImpl(ListEnvironmentsUseCase):
    """Lists execution environments using the requested pagination."""

    def __init__(self, environment_repository: EnvironmentPersistencePort) -> None:
        self._environment_repository = environment_repository

    async def execute(self, request: ListEnvironmentsQuery) -> Page[Environment]:
        """Return environments for the requested page."""
        return await self._environment_repository.find_page(request.pagination)
