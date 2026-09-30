"""Shared projection and project access behavior for Viewer use cases."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.commons.pagination import MAX_PAGE_LIMIT, PaginationParams
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.model.viewer.records import (
    SyncStatus,
    ViewerEntityType,
    ViewerSyncRecord,
    ViewerType,
)
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (  # noqa: E501
    TestCasePersistencePort,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (  # noqa: E501
    TestPlanPersistencePort,
)
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (  # noqa: E501
    TestSetPersistencePort,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)
from test_service.domain.ports.output.viewer.viewer_drift_detector_port import (
    ViewerDriftDetectorPort,
)
from test_service.domain.ports.output.viewer.viewer_publisher_port import ViewerPublisherPort


class ViewerProjectionService:
    """Build local Viewer projection work from active project snapshots."""

    def __init__(
        self,
        project_repository: ProjectPersistencePort,
        test_case_repository: TestCasePersistencePort,
        precondition_repository: PreconditionPersistencePort,
        test_set_repository: TestSetPersistencePort,
        test_plan_repository: TestPlanPersistencePort,
        viewer_repository: ViewerPersistencePort,
        viewer_publisher: ViewerPublisherPort,
        viewer_drift_detector: ViewerDriftDetectorPort,
    ) -> None:
        self._project_repository = project_repository
        self._test_case_repository = test_case_repository
        self._precondition_repository = precondition_repository
        self._test_set_repository = test_set_repository
        self._test_plan_repository = test_plan_repository
        self._viewer_repository = viewer_repository
        self._viewer_publisher = viewer_publisher
        self._viewer_drift_detector = viewer_drift_detector

    async def publish(
        self, project_key: str, viewer_type: ViewerType
    ) -> tuple[ViewerSyncRecord, ...]:
        """Queue projections for every active snapshot in an existing project."""
        await self.ensure_project(project_key)
        records: list[ViewerSyncRecord] = []
        for entity_type, entity_key, identifier in await self._active_snapshots(project_key):
            record = ViewerSyncRecord(
                identifier=uuid4(),
                project_key=project_key,
                entity_type=entity_type,
                entity_key=entity_key,
                projected_version_id=identifier,
                viewer_type=viewer_type,
                external_entity_key=entity_key,
                sync_status=SyncStatus.PENDING,
                created_at=datetime.now(UTC),
            )
            persisted_record = await self._viewer_repository.save_sync_record(record)
            try:
                await self._viewer_publisher.publish(persisted_record)
            except Exception:
                persisted_record = replace(persisted_record, sync_status=SyncStatus.ERROR)
            else:
                persisted_record = replace(
                    persisted_record,
                    sync_status=SyncStatus.SYNCED,
                    last_synced_at=datetime.now(UTC),
                )
            records.append(await self._viewer_repository.save_sync_record(persisted_record))
        return tuple(records)

    async def check_drift(self, project_key: str, viewer_type: ViewerType):
        """Check the selected external Viewer for drift in its project projections."""
        await self.ensure_project(project_key)
        offset = 0
        while True:
            pagination = PaginationParams(offset=offset, limit=MAX_PAGE_LIMIT)
            page = await self._viewer_repository.find_sync_records_page_by_project(
                project_key, pagination, viewer_type
            )
            for record in page.items:
                try:
                    await self._viewer_drift_detector.check_drift(record)
                except Exception:
                    await self._viewer_repository.save_sync_record(
                        replace(record, sync_status=SyncStatus.ERROR)
                    )
                else:
                    await self._viewer_repository.save_sync_record(
                        replace(record, last_checked_at=datetime.now(UTC))
                    )
            offset += len(page.items)
            if offset >= page.total:
                return ()

    async def ensure_project(self, project_key: str) -> None:
        """Raise a not-found error when the owning project does not exist."""
        if await self._project_repository.find_by_key(project_key) is None:
            raise EntityNotFoundException("project", project_key)

    async def _active_snapshots(self, project_key: str):
        test_cases = await self._all_active(self._test_case_repository, project_key)
        preconditions = await self._all_active(self._precondition_repository, project_key)
        test_sets = await self._all_active(self._test_set_repository, project_key)
        test_plans = await self._all_active(self._test_plan_repository, project_key)
        return (
            tuple(
                (ViewerEntityType.TEST_CASE, item.test_key, item.identifier) for item in test_cases
            )
            + tuple(
                (ViewerEntityType.PRECONDITION, item.precondition_key, item.identifier)
                for item in preconditions
            )
            + tuple(
                (ViewerEntityType.TEST_SET, item.set_key, item.identifier) for item in test_sets
            )
            + tuple(
                (ViewerEntityType.TEST_PLAN, item.plan_key, item.identifier) for item in test_plans
            )
        )

    @staticmethod
    async def _all_active(repository, project_key: str):
        offset = 0
        items = []
        while True:
            page = await repository.find_page(
                project_key,
                PaginationParams(offset=offset, limit=MAX_PAGE_LIMIT),
                VersionStatus.ACTIVE,
            )
            items.extend(page.items)
            offset += len(page.items)
            if offset >= page.total:
                return tuple(items)
