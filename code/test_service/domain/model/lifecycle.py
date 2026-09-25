"""Shared lifecycle value objects for immutable domain snapshots."""

from enum import StrEnum

from test_service.domain.model.exceptions.domain_exception import BusinessRuleViolationException


class VersionStatus(StrEnum):
    """Lifecycle state of a versioned immutable snapshot.
        DRAFT -> ACTIVE -> DEPRECATED

    Attributes:
        DRAFT: Snapshot can be prepared but not selected by consumers.
        ACTIVE: Snapshot can be selected by consumers.
        DEPRECATED: Snapshot is retained only for historical traceability.
    """

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


def activate_status(status: VersionStatus) -> VersionStatus:
    """Return the active state for a draft snapshot.

    Args:
        status: Current lifecycle state.

    Returns:
        The ``ACTIVE`` lifecycle state.

    Raises:
        BusinessRuleViolationException: If the snapshot is not a draft.
    """
    if status is not VersionStatus.DRAFT:
        raise BusinessRuleViolationException(
            "only draft snapshots can be activated",
            "INVALID_LIFECYCLE_TRANSITION",
        )
    return VersionStatus.ACTIVE


def deprecate_status(status: VersionStatus) -> VersionStatus:
    """Return the deprecated state for an active snapshot.

    Args:
        status: Current lifecycle state.

    Returns:
        The ``DEPRECATED`` lifecycle state.

    Raises:
        BusinessRuleViolationException: If the snapshot is not active.
    """
    if status is not VersionStatus.ACTIVE:
        raise BusinessRuleViolationException(
            "only active snapshots can be deprecated",
            "INVALID_LIFECYCLE_TRANSITION",
        )
    return VersionStatus.DEPRECATED
