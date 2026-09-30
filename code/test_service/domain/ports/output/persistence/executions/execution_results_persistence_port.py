"""Execution result persistence contract."""

from typing import Protocol
from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.execution.execution import (
    ActionResult,
    TestResult,
    TestResultArtifact,
)


class ExecutionResultsPersistencePort(Protocol):
    """Read contract for immutable execution result details."""

    async def find_result(self, identifier: UUID) -> TestResult | None:
        """Find a test result by UUID."""
        ...

    async def find_results_page(
        self, execution_id: UUID, pagination: PaginationParams
    ) -> Page[TestResult]:
        """Find test results belonging to one execution."""
        ...

    async def find_actions_page(
        self, test_result_id: UUID, pagination: PaginationParams
    ) -> Page[ActionResult]:
        """Find action results belonging to one test result."""
        ...

    async def find_artifacts_page(
        self, test_result_id: UUID, pagination: PaginationParams
    ) -> Page[TestResultArtifact]:
        """Find artifacts belonging to one test result."""
        ...
