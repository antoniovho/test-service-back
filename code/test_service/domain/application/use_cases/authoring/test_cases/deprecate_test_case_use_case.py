"""Use case implementation: deprecate Test Case."""

from test_service.domain.application.commands.authoring import DeprecateTestCaseCommand
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.authoring.test_cases.deprecate_test_case_use_case import (  # noqa: E501
    DeprecateTestCaseUseCase,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)


class DeprecateTestCaseUseCaseImpl(DeprecateTestCaseUseCase):
    """Deprecates one active Test Case snapshot."""

    def __init__(self, test_case_repository: TestCasePersistencePort) -> None:
        self._test_case_repository = test_case_repository

    async def execute(self, request: DeprecateTestCaseCommand) -> TestCase:
        """Transition the requested Test Case snapshot to deprecated."""
        test_case = await self._test_case_repository.find_by_id(request.identifier)
        if test_case is None or test_case.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test case", str(request.identifier), f"project '{request.project_key}'"
            )
        return await self._test_case_repository.save(test_case.deprecate())
