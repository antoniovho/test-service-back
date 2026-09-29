"""Use case implementation: list Test Case versions."""

from test_service.domain.application.queries.authoring import TestCaseVersionsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.ports.input.use_cases.authoring.test_cases.list_test_case_versions_use_case import (  # noqa: E501
    ListTestCaseVersionsUseCase,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)


class ListTestCaseVersionsUseCaseImpl(ListTestCaseVersionsUseCase):
    """Lists snapshots sharing a project-scoped Test Case key."""

    def __init__(self, test_case_repository: TestCasePersistencePort) -> None:
        self._test_case_repository = test_case_repository

    async def execute(self, request: TestCaseVersionsQuery) -> Page[TestCase]:
        """Return Test Case versions matching the requested filters."""
        return await self._test_case_repository.find_versions(
            request.project_key, request.test_key, request.pagination, request.status
        )
