"""Use case implementation: get Test Set."""

from test_service.domain.application.queries.composition import TestSetQuery
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.composition.test_sets.get_test_set_use_case import (
    GetTestSetUseCase,
)
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)


class GetTestSetUseCaseImpl(GetTestSetUseCase):
    """Retrieves one project-scoped Test Set snapshot."""

    def __init__(self, test_set_repository: TestSetPersistencePort) -> None:
        self._test_set_repository = test_set_repository

    async def execute(self, request: TestSetQuery) -> TestSet:
        """Return a Test Set only when it belongs to the requested project."""
        test_set = await self._test_set_repository.find_by_id(request.identifier)
        if test_set is None or test_set.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test set", str(request.identifier), f"project '{request.project_key}'"
            )
        return test_set
