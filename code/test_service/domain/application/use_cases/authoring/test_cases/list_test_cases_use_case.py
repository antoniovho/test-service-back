"""Use case implementation: list Test Cases."""

from test_service.domain.application.queries.authoring import ListTestCasesQuery
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import Page
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.ports.input.use_cases.authoring.test_cases.list_test_cases_use_case import (  # noqa: E501
    ListTestCasesUseCase,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)


class ListTestCasesUseCaseImpl(ListTestCasesUseCase):
    """Lists Test Case snapshots owned by one project."""

    def __init__(
        self, test_case_repository: TestCasePersistencePort, project_resolver: ProjectResolver
    ) -> None:
        self._test_case_repository = test_case_repository
        self._project_resolver = project_resolver

    async def execute(self, request: ListTestCasesQuery) -> Page[TestCase]:
        """Return Test Case snapshots matching the requested filters."""
        await self._project_resolver.resolve(request.project_key)
        return await self._test_case_repository.find_page(
            request.project_key, request.pagination, request.status
        )
