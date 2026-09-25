"""Commands for test composition use cases."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from test_service.domain.model.composition.test_plan import ExecutionMode


@dataclass(frozen=True, slots=True)
class CreateTestSetCommand:
    """Request to create a draft TestSet snapshot.

    Args:
        project_key: Owning project key.
        set_key: Stable logical test set key.
        name: Human-readable name.
        items: Ordered test case snapshot UUIDs.
        requested_by: Identity creating the snapshot.
        requested_at: Creation timestamp.
        description: Optional test set purpose.
    """

    project_key: str
    set_key: str
    name: str
    items: tuple[UUID, ...]
    requested_by: str
    requested_at: datetime
    description: str | None = None


@dataclass(frozen=True, slots=True)
class CreateTestSetVersionCommand:
    """Request to create a new TestSet version from an existing snapshot.

    Args:
        source_id: UUID of the snapshot version selected as the version's parent.
        project_key: Owning project key.
        set_key: Stable logical test set key.
        name: Human-readable name.
        items: Ordered test case snapshot UUIDs.
        requested_by: Identity creating the snapshot.
        requested_at: Creation timestamp.
        description: Optional test set purpose.
    """

    source_id: UUID
    project_key: str
    set_key: str
    name: str
    items: tuple[UUID, ...]
    requested_by: str
    requested_at: datetime
    description: str | None = None


@dataclass(frozen=True, slots=True)
class CreateTestPlanCommand:
    """Request to create a draft TestPlan snapshot.

    Args:
        project_key: Owning project key.
        plan_key: Stable logical test plan key.
        name: Human-readable name.
        execution_mode: Plan scheduling mode.
        timeout_seconds: Maximum plan execution time.
        requested_by: Identity creating the snapshot.
        requested_at: Creation timestamp.
        test_set_ids: Ordered test set snapshot UUIDs.
        test_case_ids: Ordered individual test case snapshot UUIDs.
        exclusions: Test case snapshots excluded from execution.
        description: Optional plan purpose.
        max_parallelism: Required maximum concurrency for parallel plans.
    """

    project_key: str
    plan_key: str
    name: str
    execution_mode: ExecutionMode
    timeout_seconds: int
    requested_by: str
    requested_at: datetime
    test_set_ids: tuple[UUID, ...] = ()
    test_case_ids: tuple[UUID, ...] = ()
    exclusions: tuple[UUID, ...] = ()
    description: str | None = None
    max_parallelism: int | None = None


@dataclass(frozen=True, slots=True)
class CreateTestPlanVersionCommand:
    """Request to create a new TestPlan version from an existing snapshot.

    Args:
        source_id: UUID of the snapshot version selected as the version's parent.
        project_key: Owning project key.
        plan_key: Stable logical test plan key.
        name: Human-readable name.
        execution_mode: Plan scheduling mode.
        timeout_seconds: Maximum plan execution time.
        requested_by: Identity creating the snapshot.
        requested_at: Creation timestamp.
        test_set_ids: Ordered test set snapshot UUIDs.
        test_case_ids: Ordered individual test case snapshot UUIDs.
        exclusions: Test case snapshots excluded from execution.
        description: Optional plan purpose.
        max_parallelism: Required maximum concurrency for parallel plans.
    """

    source_id: UUID
    project_key: str
    plan_key: str
    name: str
    execution_mode: ExecutionMode
    timeout_seconds: int
    requested_by: str
    requested_at: datetime
    test_set_ids: tuple[UUID, ...] = ()
    test_case_ids: tuple[UUID, ...] = ()
    exclusions: tuple[UUID, ...] = ()
    description: str | None = None
    max_parallelism: int | None = None


@dataclass(frozen=True, slots=True)
class ActivateTestSetCommand:
    """Request to activate a draft TestSet snapshot.

    Args:
        identifier: UUID of the snapshot.
        reason: Optional audit reason.
    """

    identifier: UUID
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class DeprecateTestSetCommand:
    """Request to deprecate an active TestSet snapshot.

    Args:
        identifier: UUID of the snapshot.
        reason: Optional audit reason.
    """

    identifier: UUID
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ActivateTestPlanCommand:
    """Request to activate a draft TestPlan snapshot.

    Args:
        identifier: UUID of the snapshot.
        reason: Optional audit reason.
    """

    identifier: UUID
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class DeprecateTestPlanCommand:
    """Request to deprecate an active TestPlan snapshot.

    Args:
        identifier: UUID of the snapshot.
        reason: Optional audit reason.
    """

    identifier: UUID
    reason: str | None = None
