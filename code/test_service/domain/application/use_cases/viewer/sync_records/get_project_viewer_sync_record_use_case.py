"""Use case implementation: get a project-scoped current Viewer sync record."""

from uuid import UUID

from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.viewer.records import ViewerSyncRecord
from test_service.domain.ports.input.use_cases.viewer.sync_records.get_project_viewer_sync_record_use_case import (  # noqa: E501
    GetProjectViewerSyncRecordUseCase,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)


class GetProjectViewerSyncRecordUseCaseImpl(GetProjectViewerSyncRecordUseCase):
    """Get current sync state while enforcing ownership by the requested project."""

    def __init__(
        self, project_resolver: ProjectResolver, viewer_repository: ViewerPersistencePort
    ) -> None:
        self._project_resolver = project_resolver
        self._viewer_repository = viewer_repository

    async def execute(self, request: tuple[str, UUID]) -> ViewerSyncRecord:
        project_key, sync_record_id = request
        await self._project_resolver.resolve(project_key)
        record = await self._viewer_repository.get_sync_record(sync_record_id)
        if record is None or record.project_key != project_key:
            raise EntityNotFoundException("viewer sync record", str(sync_record_id), project_key)
        return record
