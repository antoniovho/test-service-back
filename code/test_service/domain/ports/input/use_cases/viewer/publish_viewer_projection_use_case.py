"""Input port: publish viewer projection."""

from typing import Protocol

from test_service.domain.application.commands.viewer import PublishViewerProjectionCommand
from test_service.domain.model.viewer.records import ViewerSyncRecord
from test_service.domain.ports.input.use_case import AsyncUseCase


class PublishViewerProjectionUseCase(
    AsyncUseCase[PublishViewerProjectionCommand, tuple[ViewerSyncRecord, ...]], Protocol
):
    """Input port for publishing the ACTIVE version of every project entity to the viewer."""
