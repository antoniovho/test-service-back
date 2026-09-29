"""Input port: list viewer drift events for one project."""

from typing import Protocol

from test_service.domain.application.queries.viewer import ListProjectViewerDriftEventsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import DriftEvent
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListProjectViewerDriftEventsUseCase(
    AsyncUseCase[ListProjectViewerDriftEventsQuery, Page[DriftEvent]], Protocol
):
    """Input port for listing Viewer drift events owned by one project."""
