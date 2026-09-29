"""Use case implementation: activate Test Case."""

from test_service.domain.application.commands.authoring import ActivateTestCaseCommand
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.authoring.test_cases.activate_test_case_use_case import (  # noqa: E501
    ActivateTestCaseUseCase,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)


class ActivateTestCaseUseCaseImpl(ActivateTestCaseUseCase):
    """Activates one draft Test Case snapshot."""

    def __init__(self, test_case_repository: TestCasePersistencePort) -> None:
        self._test_case_repository = test_case_repository

    async def execute(self, request: ActivateTestCaseCommand) -> TestCase:
        """Transition the requested Test Case snapshot to active."""
        test_case = await self._test_case_repository.find_by_id(request.identifier)
        if test_case is None:
            raise EntityNotFoundException("test case", str(request.identifier))
        return await self._test_case_repository.save(test_case.activate())
