"""External Viewer drift detection contract."""

from typing import Protocol

from test_service.domain.model.viewer.records import ViewerSyncRecord


class ViewerDriftDetectorPort(Protocol):
    """Check whether an external Viewer projection has drifted."""

    async def check_drift(self, record: ViewerSyncRecord) -> None:
        """Check one Viewer synchronization record for external drift."""
        ...
