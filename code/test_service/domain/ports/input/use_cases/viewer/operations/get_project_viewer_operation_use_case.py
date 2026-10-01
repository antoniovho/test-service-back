"""Input port for obtaining a project-scoped Viewer operation."""

from typing import Protocol
from uuid import UUID

from test_service.domain.model.viewer.records import ViewerOperation
from test_service.domain.ports.input.use_case import AsyncUseCase


class GetProjectViewerOperationUseCase(AsyncUseCase[tuple[str, UUID], ViewerOperation], Protocol):
    """Get one asynchronous Viewer operation within its project scope."""
