"""Input port for obtaining a project-scoped current Viewer sync record."""

from typing import Protocol
from uuid import UUID

from test_service.domain.model.viewer.records import ViewerSyncRecord
from test_service.domain.ports.input.use_case import AsyncUseCase


class GetProjectViewerSyncRecordUseCase(AsyncUseCase[tuple[str, UUID], ViewerSyncRecord], Protocol):
    """Get current Viewer synchronization state while enforcing project scope."""
