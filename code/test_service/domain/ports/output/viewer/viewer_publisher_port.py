"""External Viewer projection publishing contract."""

from typing import Protocol

from test_service.domain.model.viewer.records import ViewerSyncRecord


class ViewerPublisherPort(Protocol):
    """Publish canonical projections to an external Viewer."""

    async def publish(self, record: ViewerSyncRecord) -> None:
        """Publish one synchronization record to the external Viewer."""
        ...
