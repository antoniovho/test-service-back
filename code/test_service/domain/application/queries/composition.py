"""Queries for test composition use cases."""

from dataclasses import dataclass
from uuid import UUID

from test_service.domain.commons.pagination import PaginationParams
from test_service.domain.model.lifecycle import VersionStatus


@dataclass(frozen=True, slots=True)
class TestSetQuery:
    """Request to retrieve a TestSet snapshot by UUID.

    Args:
        identifier: UUID of the requested TestSet snapshot.
    """

    identifier: UUID


@dataclass(frozen=True, slots=True)
class TestPlanQuery:
    """Request to retrieve a TestPlan snapshot by UUID.

    Args:
        identifier: UUID of the requested TestPlan snapshot.
    """

    identifier: UUID


@dataclass(frozen=True, slots=True)
class ListTestSetsQuery:
    """Request to list TestSet snapshots.

    Args:
        project_key: Owning project key.
        pagination: Page and ordering parameters.
        status: Optional lifecycle status filter.
    """

    project_key: str
    pagination: PaginationParams
    status: VersionStatus | None = None


@dataclass(frozen=True, slots=True)
class ListTestSetVersionsQuery:
    """Request to list versions sharing a TestSet key.

    Args:
        project_key: Owning project key.
        set_key: Stable business key of the TestSet.
        pagination: Page and ordering parameters.
        status: Optional lifecycle status filter.
    """

    project_key: str
    set_key: str
    pagination: PaginationParams
    status: VersionStatus | None = None


@dataclass(frozen=True, slots=True)
class ListTestPlansQuery:
    """Request to list TestPlan snapshots.

    Args:
        project_key: Owning project key.
        pagination: Page and ordering parameters.
        status: Optional lifecycle status filter.
    """

    project_key: str
    pagination: PaginationParams
    status: VersionStatus | None = None


@dataclass(frozen=True, slots=True)
class ListTestPlanVersionsQuery:
    """Request to list versions sharing a TestPlan key.

    Args:
        project_key: Owning project key.
        plan_key: Stable business key of the TestPlan.
        pagination: Page and ordering parameters.
        status: Optional lifecycle status filter.
    """

    project_key: str
    plan_key: str
    pagination: PaginationParams
    status: VersionStatus | None = None
