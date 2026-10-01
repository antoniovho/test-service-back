"""External Viewer drift detection contract."""

from typing import Protocol

from test_service.domain.model.viewer.records import DriftObservation, ViewerSyncRecord


class ViewerDriftDetectorPort(Protocol):
    """Check whether an external Viewer projection has drifted."""

    async def check_drift(self, record: ViewerSyncRecord) -> DriftObservation | None:
        """Return a normalized drift observation, when the projection diverges."""
        ...
