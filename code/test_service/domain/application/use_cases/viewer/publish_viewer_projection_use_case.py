"""Use case implementation: publish Viewer projections."""

from test_service.domain.application.commands.viewer import PublishViewerProjectionCommand
from test_service.domain.application.services.viewer_projection_service import (
    ViewerProjectionService,
)
from test_service.domain.model.viewer.records import ViewerSyncRecord
from test_service.domain.ports.input.use_cases.viewer.publish_viewer_projection_use_case import (  # noqa: E501
    PublishViewerProjectionUseCase,
)


class PublishViewerProjectionUseCaseImpl(PublishViewerProjectionUseCase):
    """Queue Viewer projections for active project snapshots."""

    def __init__(self, projection_service: ViewerProjectionService) -> None:
        self._projection_service = projection_service

    async def execute(
        self, request: PublishViewerProjectionCommand
    ) -> tuple[ViewerSyncRecord, ...]:
        """Persist pending projection records for the requested project."""
        return await self._projection_service.publish(request.project_key, request.viewer_type)
