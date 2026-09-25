"""Immutable TestCase snapshot aggregate."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from test_service.domain.commons.immutable import freeze_mapping
from test_service.domain.model.authoring.definition import Definition
from test_service.domain.model.exceptions.domain_exception import BusinessRuleViolationException
from test_service.domain.model.lifecycle import VersionStatus, activate_status, deprecate_status


class TestType(StrEnum):
    """Execution modality of a test case.

    Attributes:
        AUTOMATED: The runner performs the test definition.
        MANUAL: A human performs the test definition.
    """

    AUTOMATED = "AUTOMATED"
    MANUAL = "MANUAL"


class TestLevel(StrEnum):
    """Quality classification for a test case.

    Attributes:
        FUNCTIONAL: Verifies expected functional behavior.
        ERROR: Verifies expected error behavior.
        INTEGRATION: Verifies integration behavior.
        PERFORMANCE: Verifies performance characteristics.
        SECURITY: Verifies security characteristics.
        STRESS: Verifies behavior under stress.
    """

    FUNCTIONAL = "FUNCTIONAL"
    ERROR = "ERROR"
    INTEGRATION = "INTEGRATION"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    STRESS = "STRESS"


class Priority(StrEnum):
    """Business priority of a test case.

    Attributes:
        LOW: Lowest business priority.
        MEDIUM: Standard business priority.
        HIGH: High business priority.
        CRITICAL: Critical business priority.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class PreconditionReference:
    """Exact precondition version required before a test case runs.

    Args:
        identifier: UUID of the immutable precondition snapshot.
        precondition_key: Stable key of the referenced precondition.
        version: Referenced positive snapshot version.
    """

    identifier: UUID
    precondition_key: str
    version: int


@dataclass(frozen=True, slots=True)
class TestCase:
    """Immutable authored test case snapshot.

    Args:
        identifier: UUID of this immutable snapshot.
        project_key: Owning project key.
        test_key: Stable logical test case key.
        version: Positive version number of this snapshot.
        name: Human-readable test case name.
        summary: Concise scenario summary.
        objective: Expected outcome of the test.
        test_type: Execution modality.
        test_level: Quality classification.
        priority: Business priority.
        definition: Ordered executable definition.
        timeout_seconds: Maximum execution time.
        created_at: Creation timestamp.
        created_by: Identity that created the snapshot.
        preconditions: Ordered precondition snapshots required before execution.
        status: Snapshot lifecycle state.
        metadata: Additional safe domain metadata.

    Raises:
        BusinessRuleViolationException:
            If version, timeout, or referenced preconditions are invalid.
    """

    identifier: UUID
    project_key: str
    test_key: str
    version: int
    name: str
    summary: str
    objective: str
    test_type: TestType
    test_level: TestLevel
    priority: Priority
    definition: Definition
    timeout_seconds: int
    created_at: datetime
    created_by: str
    preconditions: tuple[PreconditionReference, ...] = ()
    status: VersionStatus = VersionStatus.DRAFT
    metadata: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        """Validate immutable TestCase invariants and freeze mutable metadata.

        Raises:
            BusinessRuleViolationException: If version, timeout, or references are invalid.
        """
        if self.version < 1 or self.timeout_seconds < 1:
            raise BusinessRuleViolationException(
                "version and timeout must be positive",
                "INVALID_TEST_CASE",
            )
        references = {reference.identifier for reference in self.preconditions}
        if len(references) != len(self.preconditions):
            raise BusinessRuleViolationException(
                "test case preconditions must reference distinct snapshots",
                "INVALID_TEST_CASE",
            )
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))

    def activate(self) -> "TestCase":
        """Return this snapshot in the active state.

        Returns:
            A new active test case snapshot.

        Raises:
            BusinessRuleViolationException: If this snapshot is not a draft.
        """
        return replace(self, status=activate_status(self.status))

    def deprecate(self) -> "TestCase":
        """Return this snapshot in the deprecated state.

        Returns:
            A new deprecated test case snapshot.

        Raises:
            BusinessRuleViolationException: If this snapshot is not active.
        """
        return replace(self, status=deprecate_status(self.status))
