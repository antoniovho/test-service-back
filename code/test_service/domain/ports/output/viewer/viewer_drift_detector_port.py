"""External Viewer drift detection contract."""

from typing import Protocol

from test_service.domain.model.viewer.projection import ViewerProjection
from test_service.domain.model.viewer.records import DriftObservation


class ViewerDriftDetectorPort(Protocol):
    """Check whether an external Viewer projection has drifted."""

    async def check_drift(self, projection: ViewerProjection) -> DriftObservation | None:
        """Return a normalized drift observation, when the projection diverges."""
        ...
