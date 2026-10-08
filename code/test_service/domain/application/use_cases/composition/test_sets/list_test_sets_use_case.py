"""Use case implementation: list Test Sets."""

from test_service.domain.application.queries.composition import ListTestSetsQuery
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import Page
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.ports.input.use_cases.composition.test_sets.list_test_sets_use_case import (  # noqa: E501
    ListTestSetsUseCase,
)
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)


class ListTestSetsUseCaseImpl(ListTestSetsUseCase):
    """Lists Test Set snapshots owned by one project."""

    def __init__(
        self, test_set_repository: TestSetPersistencePort, project_resolver: ProjectResolver
    ) -> None:
        self._test_set_repository = test_set_repository
        self._project_resolver = project_resolver

    async def execute(self, request: ListTestSetsQuery) -> Page[TestSet]:
        """Return the requested project-scoped Test Set page."""
        await self._project_resolver.resolve(request.project_key)
        return await self._test_set_repository.find_page(
            request.project_key, request.pagination, request.status
        )
