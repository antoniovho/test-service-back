"""Viewer projection and drift-record domain models."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from test_service.domain.commons.immutable import freeze_mapping


class ViewerEntityType(StrEnum):
    """Domain snapshot types allowed in a Viewer projection.

    Attributes:
        TEST_CASE: A test case snapshot.
        PRECONDITION: A precondition snapshot.
        TEST_SET: A test set snapshot.
        TEST_PLAN: A test plan snapshot.
    """

    TEST_CASE = "TEST_CASE"
    PRECONDITION = "PRECONDITION"
    TEST_SET = "TEST_SET"
    TEST_PLAN = "TEST_PLAN"


class ViewerType(StrEnum):
    """Supported external viewer platforms.

    Attributes:
        XRAY: Xray external test viewer.
    """

    XRAY = "XRAY"


class SyncStatus(StrEnum):
    """Lifecycle state of a Viewer projection.

    Attributes:
        PENDING: Projection request awaits completion.
        SYNCED: Projection has completed successfully.
        ERROR: Projection completed with an error.
        DRIFT_DETECTED: External viewer diverged from canonical projection.
    """

    PENDING = "PENDING"
    SYNCED = "SYNCED"
    ERROR = "ERROR"
    DRIFT_DETECTED = "DRIFT_DETECTED"


class DriftType(StrEnum):
    """Type of external divergence.

    Attributes:
        MODIFIED: External entity was changed.
        DELETED: External entity was deleted.
        MISSING: Expected external entity is missing.
    """

    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    MISSING = "MISSING"


class NotificationStatus(StrEnum):
    """Lifecycle of a drift notification.

    Attributes:
        PENDING: Notification has not been delivered.
        SENT: Notification was delivered.
        ERROR: Notification delivery failed.
    """

    PENDING = "PENDING"
    SENT = "SENT"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class ViewerSyncRecord:
    """Canonical projection state for one external Viewer entity.

    Args:
        identifier: UUID of the synchronization record.
        entity_type: Type of projected immutable snapshot.
        entity_key: Stable logical key of the entity.
        projected_version_id: UUID of the projected snapshot.
        viewer_type: External Viewer platform.
        external_entity_key: Stable external viewer key.
        sync_status: Current synchronization status.
        created_at: Record creation timestamp.
        external_entity_id: Optional technical external identifier.
        last_synced_at: Optional successful synchronization timestamp.
        last_checked_at: Optional drift check timestamp.
    """

    identifier: UUID
    entity_type: ViewerEntityType
    entity_key: str
    projected_version_id: UUID
    viewer_type: ViewerType
    external_entity_key: str
    sync_status: SyncStatus
    created_at: datetime
    external_entity_id: str | None = None
    last_synced_at: datetime | None = None
    last_checked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class DriftEvent:
    """Immutable observation of Viewer divergence.

    Args:
        identifier: UUID of the event.
        sync_record_id: UUID of the affected synchronization record.
        projected_version_id: UUID of the expected snapshot.
        detected_at: Timestamp of detection.
        drift_type: External divergence classification.
        notification_status: Notification delivery state.
        details: Optional safe, bounded structured difference details.
    """

    identifier: UUID
    sync_record_id: UUID
    projected_version_id: UUID
    detected_at: datetime
    drift_type: DriftType
    notification_status: NotificationStatus
    details: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        """Freeze the mutable details mapping."""
        object.__setattr__(self, "details", freeze_mapping(self.details))
