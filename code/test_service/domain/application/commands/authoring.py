"""Commands for immutable authoring use cases."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from test_service.domain.model.authoring.definition import Definition
from test_service.domain.model.authoring.test_case import (
    PreconditionReference,
    Priority,
    TestLevel,
    TestType,
)


@dataclass(frozen=True, slots=True)
class CreateTestCaseCommand:
    """Request to create a draft TestCase snapshot.

    Args:
        project_key: Owning project key.
        test_key: Stable logical test case key.
        name: Human-readable name.
        summary: Concise scenario summary.
        objective: Expected scenario outcome.
        test_type: Execution modality.
        test_level: Quality classification.
        priority: Business priority.
        definition: Executable definition.
        timeout_seconds: Maximum execution time.
        requested_by: Identity creating the snapshot.
        requested_at: Creation timestamp.
        preconditions: Ordered precondition snapshot references.
        metadata: Optional safe metadata.
    """

    project_key: str
    test_key: str
    name: str
    summary: str
    objective: str
    test_type: TestType
    test_level: TestLevel
    priority: Priority
    definition: Definition
    timeout_seconds: int
    requested_by: str
    requested_at: datetime
    preconditions: tuple[PreconditionReference, ...] = ()
    metadata: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CreateTestCaseVersionCommand:
    """Request to create a new TestCase version from an existing snapshot.

    Args:
        source_id: UUID of the snapshot version selected as the version's parent.
        project_key: Owning project key.
        test_key: Stable logical test case key.
        name: Human-readable name.
        summary: Concise scenario summary.
        objective: Expected scenario outcome.
        test_type: Execution modality.
        test_level: Quality classification.
        priority: Business priority.
        definition: Executable definition.
        timeout_seconds: Maximum execution time.
        requested_by: Identity creating the snapshot.
        requested_at: Creation timestamp.
        preconditions: Ordered precondition snapshot references.
        metadata: Optional safe metadata.
    """

    source_id: UUID
    project_key: str
    test_key: str
    name: str
    summary: str
    objective: str
    test_type: TestType
    test_level: TestLevel
    priority: Priority
    definition: Definition
    timeout_seconds: int
    requested_by: str
    requested_at: datetime
    preconditions: tuple[PreconditionReference, ...] = ()
    metadata: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CreatePreconditionCommand:
    """Request to create a draft Precondition snapshot.

    Args:
        project_key: Owning project key.
        precondition_key: Stable logical precondition key.
        name: Human-readable name.
        description: Prerequisite purpose.
        validation_definition: Executable validation definition.
        requested_by: Identity creating the snapshot.
        requested_at: Creation timestamp.
        metadata: Optional safe metadata.
    """

    project_key: str
    precondition_key: str
    name: str
    description: str
    validation_definition: Definition
    requested_by: str
    requested_at: datetime
    metadata: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CreatePreconditionVersionCommand:
    """Request to create a new Precondition version from an existing snapshot.

    Args:
        source_id: UUID of the snapshot version selected as the version's parent.
        project_key: Owning project key.
        precondition_key: Stable logical precondition key.
        name: Human-readable name.
        description: Prerequisite purpose.
        validation_definition: Executable validation definition.
        requested_by: Identity creating the snapshot.
        requested_at: Creation timestamp.
        metadata: Optional safe metadata.
    """

    source_id: UUID
    project_key: str
    precondition_key: str
    name: str
    description: str
    validation_definition: Definition
    requested_by: str
    requested_at: datetime
    metadata: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ActivateTestCaseCommand:
    """Request to activate a draft TestCase snapshot.

    Args:
        identifier: UUID of the snapshot.
        reason: Optional audit reason.
    """

    identifier: UUID
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class DeprecateTestCaseCommand:
    """Request to deprecate an active TestCase snapshot.

    Args:
        identifier: UUID of the snapshot.
        reason: Optional audit reason.
    """

    identifier: UUID
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ActivatePreconditionCommand:
    """Request to activate a draft Precondition snapshot.

    Args:
        identifier: UUID of the snapshot.
        reason: Optional audit reason.
    """

    identifier: UUID
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class DeprecatePreconditionCommand:
    """Request to deprecate an active Precondition snapshot.

    Args:
        identifier: UUID of the snapshot.
        reason: Optional audit reason.
    """

    identifier: UUID
    reason: str | None = None
