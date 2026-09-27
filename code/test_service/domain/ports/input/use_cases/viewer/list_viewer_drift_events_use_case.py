"""Input port: list viewer drift events across all projects."""

from typing import Protocol

from test_service.domain.application.queries.viewer import ListViewerDriftEventsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import DriftEvent
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListViewerDriftEventsUseCase(
    AsyncUseCase[ListViewerDriftEventsQuery, Page[DriftEvent]], Protocol
):
    """Input port for listing Viewer drift events across every project."""
