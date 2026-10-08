"""Persistence adapter for immutable execution evidence."""
# ruff: noqa: E501

from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.execution.execution import (
    ActionResult,
    TestResult,
    TestResultArtifact,
)
from test_service.domain.ports.output.persistence.executions.execution_results_persistence_port import (  # noqa: E501
    ExecutionResultsPersistencePort,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.mappers.execution_results_persistence_mapper import (  # noqa: E501
    ExecutionResultsPersistenceMapper,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.repositories.execution_results_repository import (  # noqa: E501
    ExecutionResultsRepository,
)


class ExecutionResultsPersistenceAdapter(ExecutionResultsPersistencePort):
    """Adapt immutable evidence persistence into domain result models."""

    def __init__(self, repository: ExecutionResultsRepository) -> None:
        self._repository = repository

    async def save_results(
        self,
        result: TestResult,
        actions: tuple[ActionResult, ...],
        artifacts: tuple[TestResultArtifact, ...] = (),
    ) -> None:
        await self._repository.save_results(
            ExecutionResultsPersistenceMapper.to_test_result_dto(result),
            tuple(
                ExecutionResultsPersistenceMapper.to_action_result_dto(action) for action in actions
            ),
            tuple(
                ExecutionResultsPersistenceMapper.to_artifact_dto(artifact)
                for artifact in artifacts
            ),
        )

    async def find_result(self, identifier: UUID) -> TestResult | None:
        """Find one result or return ``None`` when absent."""
        dto = await self._repository.find_result(identifier)
        return ExecutionResultsPersistenceMapper.to_test_result(dto) if dto is not None else None

    async def find_results_page(
        self, execution_id: UUID, pagination: PaginationParams
    ) -> Page[TestResult]:
        """Map a persisted result page to its domain equivalent."""
        page = await self._repository.find_results_page(execution_id, pagination)
        return Page(
            items=tuple(
                ExecutionResultsPersistenceMapper.to_test_result(dto) for dto in page.items
            ),
            total=page.total,
        )

    async def find_actions_page(
        self, test_result_id: UUID, pagination: PaginationParams
    ) -> Page[ActionResult]:
        """Map a persisted action page to its domain equivalent."""
        page = await self._repository.find_actions_page(test_result_id, pagination)
        return Page(
            items=tuple(
                ExecutionResultsPersistenceMapper.to_action_result(dto) for dto in page.items
            ),
            total=page.total,
        )

    async def find_artifacts_page(
        self, test_result_id: UUID, pagination: PaginationParams
    ) -> Page[TestResultArtifact]:
        """Map a persisted artifact page to its domain equivalent."""
        page = await self._repository.find_artifacts_page(test_result_id, pagination)
        return Page(
            items=tuple(ExecutionResultsPersistenceMapper.to_artifact(dto) for dto in page.items),
            total=page.total,
        )
