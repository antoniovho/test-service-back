"""Shared lifecycle value objects for immutable domain snapshots."""

from enum import StrEnum

from test_service.domain.model.exceptions.invalid_lifecycle_transition_exception import (
    InvalidLifecycleTransitionException,
)


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
        InvalidLifecycleTransitionException: If the snapshot is not a draft.
    """
    if status is not VersionStatus.DRAFT:
        raise InvalidLifecycleTransitionException("only draft snapshots can be activated")
    return VersionStatus.ACTIVE


def deprecate_status(status: VersionStatus) -> VersionStatus:
    """Return the deprecated state for an active snapshot.

    Args:
        status: Current lifecycle state.

    Returns:
        The ``DEPRECATED`` lifecycle state.

    Raises:
        InvalidLifecycleTransitionException: If the snapshot is not active.
    """
    if status is not VersionStatus.ACTIVE:
        raise InvalidLifecycleTransitionException("only active snapshots can be deprecated")
    return VersionStatus.DEPRECATED
