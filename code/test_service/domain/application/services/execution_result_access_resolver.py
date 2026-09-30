"""Resolution of immutable test results scoped to their execution."""

from uuid import UUID

from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.execution.execution import TestResult
from test_service.domain.ports.output.persistence.executions.execution_results_persistence_port import (  # noqa: E501
    ExecutionResultsPersistencePort,
)


class ExecutionResultAccessResolver:
    """Resolve test results while enforcing their execution ownership."""

    def __init__(self, execution_results_repository: ExecutionResultsPersistencePort) -> None:
        self._execution_results_repository = execution_results_repository

    async def resolve(self, execution_id: UUID, test_result_id: UUID) -> TestResult:
        """Return the result only when it belongs to the requested execution."""
        test_result = await self._execution_results_repository.find_result(test_result_id)
        if test_result is None or test_result.execution_id != execution_id:
            raise EntityNotFoundException(
                "test result", str(test_result_id), f"execution '{execution_id}'"
            )
        return test_result
