"""Resolution of project-scoped execution resources."""

from uuid import UUID

from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.execution.execution import Execution
from test_service.domain.ports.output.persistence.executions.execution_persistence_port import (  # noqa: E501
    ExecutionPersistencePort,
)


class ExecutionAccessResolver:
    """Resolve executions while enforcing their project ownership."""

    def __init__(self, execution_repository: ExecutionPersistencePort) -> None:
        self._execution_repository = execution_repository

    async def resolve(self, project_key: str, execution_id: UUID) -> Execution:
        """Return the execution only when it belongs to the requested project."""
        execution = await self._execution_repository.find_execution(execution_id)
        if execution is None or execution.project_key != project_key:
            raise EntityNotFoundException(
                "execution", str(execution_id), f"project '{project_key}'"
            )
        return execution
