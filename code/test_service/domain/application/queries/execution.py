"""Queries for execution use cases."""

from dataclasses import dataclass
from uuid import UUID

from test_service.domain.commons.pagination import PaginationParams


@dataclass(frozen=True, slots=True)
class EnvironmentQuery:
    """Request to retrieve an Environment by UUID.

    Args:
        identifier: UUID of the requested Environment.
    """

    identifier: UUID


@dataclass(frozen=True, slots=True)
class ExecutionQuery:
    """Request to retrieve an Execution by UUID.

    Args:
        identifier: UUID of the requested Execution.
    """

    identifier: UUID


@dataclass(frozen=True, slots=True)
class ListEnvironmentsQuery:
    """Request to list environments.

    Args:
        pagination: Page and ordering parameters.
    """

    pagination: PaginationParams


@dataclass(frozen=True, slots=True)
class ListExecutionsQuery:
    """Request to list executions for a project.

    Args:
        project_key: Owning project key.
        pagination: Page and ordering parameters.
    """

    project_key: str
    pagination: PaginationParams


@dataclass(frozen=True, slots=True)
class ListExecutionResultsQuery:
    """Request to list results belonging to an execution.

    Args:
        execution_id: UUID of the owning execution.
        pagination: Page and ordering parameters.
    """

    execution_id: UUID
    pagination: PaginationParams


@dataclass(frozen=True, slots=True)
class ExecutionResultQuery:
    """Request to retrieve one result belonging to an execution.

    Args:
        execution_id: UUID of the owning execution.
        test_result_id: UUID of the requested test result.
    """

    execution_id: UUID
    test_result_id: UUID


@dataclass(frozen=True, slots=True)
class ListExecutionResultActionsQuery:
    """Request to list action results belonging to one test result.

    Args:
        execution_id: UUID of the owning execution.
        test_result_id: UUID of the owning test result.
        pagination: Page and ordering parameters.
    """

    execution_id: UUID
    test_result_id: UUID
    pagination: PaginationParams


@dataclass(frozen=True, slots=True)
class ListExecutionResultArtifactsQuery:
    """Request to list artifacts belonging to one test result.

    Args:
        execution_id: UUID of the owning execution.
        test_result_id: UUID of the owning test result.
        pagination: Page and ordering parameters.
    """

    execution_id: UUID
    test_result_id: UUID
    pagination: PaginationParams
