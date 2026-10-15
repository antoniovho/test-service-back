"""External Viewer projection publishing contract."""

from typing import Protocol

from test_service.domain.model.viewer.projection import ViewerExternalIdentity, ViewerProjection


class ViewerPublisherPort(Protocol):
    """Publish canonical projections to an external Viewer."""

    async def publish(self, projection: ViewerProjection) -> ViewerExternalIdentity:
        """Publish one canonical projection and return its external identity."""
        ...
