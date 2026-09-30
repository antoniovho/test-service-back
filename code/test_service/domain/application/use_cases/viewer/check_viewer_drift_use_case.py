"""Use case implementation: check Viewer drift."""

from test_service.domain.application.commands.viewer import CheckViewerDriftCommand
from test_service.domain.application.services.viewer_projection_service import (
    ViewerProjectionService,
)
from test_service.domain.model.viewer.records import DriftEvent
from test_service.domain.ports.input.use_cases.viewer.check_viewer_drift_use_case import (
    CheckViewerDriftUseCase,
)


class CheckViewerDriftUseCaseImpl(CheckViewerDriftUseCase):
    """Record drift-check attempts until a remote viewer adapter is configured."""

    def __init__(self, projection_service: ViewerProjectionService) -> None:
        self._projection_service = projection_service

    async def execute(self, request: CheckViewerDriftCommand) -> tuple[DriftEvent, ...]:
        """Check local projection state and return detected external drift events."""
        return await self._projection_service.check_drift(request.project_key, request.viewer_type)
