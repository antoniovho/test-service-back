"""Use case implementation: deprecate Test Set."""

from test_service.domain.application.commands.composition import DeprecateTestSetCommand
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.composition.test_sets.deprecate_test_set_use_case import (  # noqa: E501
    DeprecateTestSetUseCase,
)
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)


class DeprecateTestSetUseCaseImpl(DeprecateTestSetUseCase):
    """Deprecates one active Test Set snapshot."""

    def __init__(self, test_set_repository: TestSetPersistencePort) -> None:
        self._test_set_repository = test_set_repository

    async def execute(self, request: DeprecateTestSetCommand) -> TestSet:
        """Transition the requested Test Set snapshot to deprecated."""
        test_set = await self._test_set_repository.find_by_id(request.identifier)
        if test_set is None or test_set.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test set", str(request.identifier), f"project '{request.project_key}'"
            )
        return await self._test_set_repository.save(test_set.deprecate())
