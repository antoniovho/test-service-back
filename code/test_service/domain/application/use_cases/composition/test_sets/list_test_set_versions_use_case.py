"""Use case implementation: list Test Set versions."""

from test_service.domain.application.queries.composition import ListTestSetVersionsQuery
from test_service.domain.application.services.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import Page
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.ports.input.use_cases.composition.test_sets.list_test_set_versions_use_case import (  # noqa: E501
    ListTestSetVersionsUseCase,
)
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)


class ListTestSetVersionsUseCaseImpl(ListTestSetVersionsUseCase):
    """Lists snapshots sharing a project-scoped Test Set key."""

    def __init__(
        self, test_set_repository: TestSetPersistencePort, project_resolver: ProjectResolver
    ) -> None:
        self._test_set_repository = test_set_repository
        self._project_resolver = project_resolver

    async def execute(self, request: ListTestSetVersionsQuery) -> Page[TestSet]:
        """Return the requested page of Test Set versions."""
        await self._project_resolver.resolve(request.project_key)
        return await self._test_set_repository.find_versions(
            request.project_key, request.set_key, request.pagination, request.status
        )
