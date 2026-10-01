"""Input port: check viewer drift."""

from typing import Protocol

from test_service.domain.application.commands.viewer import CheckViewerDriftCommand
from test_service.domain.model.viewer.records import ViewerOperation
from test_service.domain.ports.input.use_case import AsyncUseCase


class CheckViewerDriftUseCase(AsyncUseCase[CheckViewerDriftCommand, ViewerOperation], Protocol):
    """Input port for checking every published project entity for viewer drift."""
