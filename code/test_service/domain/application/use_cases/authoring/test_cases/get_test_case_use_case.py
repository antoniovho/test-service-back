"""Use case implementation: get Test Case."""

from test_service.domain.application.queries.authoring import TestCaseQuery
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.authoring.test_cases.get_test_case_use_case import (
    GetTestCaseUseCase,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)


class GetTestCaseUseCaseImpl(GetTestCaseUseCase):
    """Retrieves one Test Case snapshot by UUID."""

    def __init__(self, test_case_repository: TestCasePersistencePort) -> None:
        self._test_case_repository = test_case_repository

    async def execute(self, request: TestCaseQuery) -> TestCase:
        """Return the requested Test Case snapshot."""
        test_case = await self._test_case_repository.find_by_id(request.identifier)
        if test_case is None:
            raise EntityNotFoundException("test case", str(request.identifier))
        return test_case
