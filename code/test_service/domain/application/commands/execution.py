"""Commands for execution use cases."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from test_service.domain.model.execution.execution import TriggerType


@dataclass(frozen=True, slots=True)
class CreateEnvironmentCommand:
    """Request to create an execution environment.

    Args:
        environment_key: Stable global environment key.
        name: Human-readable environment name.
        requested_by: Identity creating the environment.
        requested_at: Creation timestamp.
        description: Optional environment purpose.
        configuration: Safe unresolved configuration values.
    """

    environment_key: str
    name: str
    requested_by: str
    requested_at: datetime
    description: str | None = None
    configuration: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ActivateEnvironmentCommand:
    """Request to mark an environment as available for new executions.

    Args:
        identifier: UUID of the environment.
        reason: Optional audit reason.
    """

    identifier: UUID
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class DeactivateEnvironmentCommand:
    """Request to mark an environment as unavailable for new executions.

    Args:
        identifier: UUID
        reason: Optional audit reason.
    """

    identifier: UUID
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ScheduleExecutionCommand:
    """Request to schedule an execution of exact snapshots.

    Args:
        test_plan_id: UUID of the active test plan snapshot.
        environment_id: UUID of the active environment.
        trigger_type: Source of the execution request.
        requested_at: Request acceptance timestamp.
        triggered_by: Optional initiating identity.
    """

    test_plan_id: UUID
    environment_id: UUID
    trigger_type: TriggerType
    requested_at: datetime
    triggered_by: str | None = None


@dataclass(frozen=True, slots=True)
class CancelExecutionCommand:
    """Request to cancel an execution that has not reached a terminal state.

    Args:
        identifier: UUID of the execution.
        reason: Optional audit reason.
    """

    identifier: UUID
    reason: str | None = None
