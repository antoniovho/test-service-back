"""Queries for immutable authoring use cases."""

from dataclasses import dataclass
from uuid import UUID

from test_service.domain.commons.pagination import PaginationParams
from test_service.domain.model.lifecycle import VersionStatus


@dataclass(frozen=True, slots=True)
class TestCaseQuery:
    """Request to retrieve a TestCase snapshot by UUID.

    Args:
        identifier: UUID of the requested TestCase snapshot.
    """

    identifier: UUID


@dataclass(frozen=True, slots=True)
class PreconditionQuery:
    """Request to retrieve a Precondition snapshot by UUID.

    Args:
        identifier: UUID of the requested Precondition snapshot.
    """

    identifier: UUID


@dataclass(frozen=True, slots=True)
class TestCaseVersionsQuery:
    """Request to list versions sharing a TestCase key.

    Args:
        project_key: Owning project key.
        test_key: Stable business key of the TestCase.
        pagination: Page and ordering parameters.
        status: Optional lifecycle status filter.
    """

    project_key: str
    test_key: str
    pagination: PaginationParams
    status: VersionStatus | None = None


@dataclass(frozen=True, slots=True)
class PreconditionVersionsQuery:
    """Request to list versions sharing a Precondition key.

    Args:
        project_key: Owning project key.
        precondition_key: Stable business key of the Precondition.
        pagination: Page and ordering parameters.
        status: Optional lifecycle status filter.
    """

    project_key: str
    precondition_key: str
    pagination: PaginationParams
    status: VersionStatus | None = None


@dataclass(frozen=True, slots=True)
class ListTestCasesQuery:
    """Request to list TestCase snapshots.

    Args:
        project_key: Owning project key.
        pagination: Page and ordering parameters.
        status: Optional lifecycle status filter.
    """

    project_key: str
    pagination: PaginationParams
    status: VersionStatus | None = None


@dataclass(frozen=True, slots=True)
class ListPreconditionsQuery:
    """Request to list Precondition snapshots.

    Args:
        project_key: Owning project key.
        pagination: Page and ordering parameters.
        status: Optional lifecycle status filter.
    """

    project_key: str
    pagination: PaginationParams
    status: VersionStatus | None = None
