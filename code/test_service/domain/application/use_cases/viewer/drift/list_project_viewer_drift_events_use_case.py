"""Use case implementation: list project Viewer drift events."""

from test_service.domain.application.queries.viewer import ListProjectViewerDriftEventsQuery
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import DriftEvent
from test_service.domain.ports.input.use_cases.viewer.drift.list_project_viewer_drift_events_use_case import (  # noqa: E501
    ListProjectViewerDriftEventsUseCase,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)


class ListProjectViewerDriftEventsUseCaseImpl(ListProjectViewerDriftEventsUseCase):
    """List drift events for one existing project."""

    def __init__(
        self, project_resolver: ProjectResolver, viewer_repository: ViewerPersistencePort
    ) -> None:
        self._project_resolver = project_resolver
        self._viewer_repository = viewer_repository

    async def execute(self, request: ListProjectViewerDriftEventsQuery) -> Page[DriftEvent]:
        await self._project_resolver.resolve(request.project_key)
        return await self._viewer_repository.find_drift_events_page_by_project(
            request.project_key, request.pagination, request.viewer_type
        )
