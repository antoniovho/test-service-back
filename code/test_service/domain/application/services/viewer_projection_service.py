"""Shared projection and project access behavior for Viewer use cases."""

import logging
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from test_service.domain.application.queries.pagination import MAX_PAGE_LIMIT, PaginationParams
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.application.services.viewer_projection_builder import (
    ViewerProjectionBuilder,
    ViewerSnapshot,
)
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.model.exceptions.viewer_projection_integrity_exception import (
    ViewerProjectionIntegrityException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.model.viewer.managed_state import ViewerManagedState
from test_service.domain.model.viewer.projection import ViewerProjection
from test_service.domain.model.viewer.records import (
    DriftEvent,
    DriftObservation,
    NotificationStatus,
    SyncStatus,
    ViewerEntityType,
    ViewerOperation,
    ViewerOperationStatus,
    ViewerOperationType,
    ViewerSyncRecord,
    ViewerType,
)
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
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

logger = logging.getLogger(__name__)


class ViewerProjectionService:
    """Build local Viewer projection work from active project snapshots."""

    def __init__(
        self,
        project_resolver: ProjectResolver,
        test_case_repository: TestCasePersistencePort,
        precondition_repository: PreconditionPersistencePort,
        test_set_repository: TestSetPersistencePort,
        test_plan_repository: TestPlanPersistencePort,
        viewer_repository: ViewerPersistencePort,
        viewer_publisher: ViewerPublisherPort,
        viewer_drift_detector: ViewerDriftDetectorPort,
    ) -> None:
        self._project_resolver = project_resolver
        self._test_case_repository = test_case_repository
        self._precondition_repository = precondition_repository
        self._test_set_repository = test_set_repository
        self._test_plan_repository = test_plan_repository
        self._viewer_repository = viewer_repository
        self._viewer_publisher = viewer_publisher
        self._viewer_drift_detector = viewer_drift_detector

    async def request_publication(
        self, project_key: str, viewer_type: ViewerType
    ) -> ViewerOperation:
        """Persist a publication request for asynchronous processing."""
        return await self._request_operation(
            project_key, viewer_type, ViewerOperationType.PUBLICATION
        )

    async def request_drift_check(
        self, project_key: str, viewer_type: ViewerType
    ) -> ViewerOperation:
        """Persist a drift-check request for asynchronous processing."""
        return await self._request_operation(
            project_key, viewer_type, ViewerOperationType.DRIFT_CHECK
        )

    async def process_next_operation(self) -> ViewerOperation | None:
        """Claim and process one pending Viewer operation."""
        operation = await self._viewer_repository.claim_next_operation()
        if operation is None:
            return None
        try:
            if operation.operation_type is ViewerOperationType.PUBLICATION:
                return await self._publish(operation)
            return await self._check_drift(operation)
        except Exception:
            logger.exception(
                "Viewer operation failed", extra={"operation_id": str(operation.identifier)}
            )
            return await self._viewer_repository.save_operation(
                replace(
                    operation,
                    status=ViewerOperationStatus.FAILED,
                    finished_at=datetime.now(UTC),
                    error="Viewer operation could not be completed.",
                )
            )

    async def _request_operation(
        self,
        project_key: str,
        viewer_type: ViewerType,
        operation_type: ViewerOperationType,
    ) -> ViewerOperation:
        await self._project_resolver.resolve_active(project_key)
        return await self._viewer_repository.save_operation(
            ViewerOperation(
                identifier=uuid4(),
                project_key=project_key,
                viewer_type=viewer_type,
                operation_type=operation_type,
                status=ViewerOperationStatus.PENDING,
                created_at=datetime.now(UTC),
            )
        )

    async def _publish(self, operation: ViewerOperation) -> ViewerOperation:
        records: list[ViewerSyncRecord] = []
        snapshots = await self._active_snapshots(operation.project_key)
        snapshots_by_id: dict[UUID, ViewerSnapshot] = {
            snapshot.identifier: snapshot for _, snapshot in snapshots
        }
        external_ids: dict[UUID, str] = {}
        for entity_type, snapshot in snapshots:
            operation = await self._heartbeat(operation)
            entity_key = snapshot.logical_key
            existing = await self._viewer_repository.find_sync_record(
                operation.project_key, entity_type, entity_key, operation.viewer_type
            )
            record = ViewerSyncRecord(
                identifier=existing.identifier if existing is not None else uuid4(),
                project_key=operation.project_key,
                entity_type=entity_type,
                entity_key=entity_key,
                projected_version_id=snapshot.identifier,
                viewer_type=operation.viewer_type,
                external_entity_key=(
                    existing.external_entity_key if existing is not None else entity_key
                ),
                sync_status=SyncStatus.PENDING,
                created_at=existing.created_at if existing is not None else datetime.now(UTC),
                operation_id=operation.identifier,
                external_entity_id=existing.external_entity_id if existing is not None else None,
            )
            persisted_record = await self._viewer_repository.save_sync_record(record)
            try:
                projection = ViewerProjectionBuilder.build(
                    persisted_record, snapshot, snapshots_by_id, external_ids
                )
                identity = await self._viewer_publisher.publish(projection)
            except Exception as error:
                logger.exception(
                    "Viewer projection failed",
                    extra={
                        "operation_id": str(operation.identifier),
                        "entity_type": entity_type.value,
                        "entity_key": entity_key,
                    },
                )
                persisted_record = replace(
                    persisted_record,
                    sync_status=SyncStatus.ERROR,
                    error=self._sync_error(error),
                )
            else:
                persisted_record = replace(
                    persisted_record,
                    sync_status=SyncStatus.SYNCED,
                    external_entity_id=identity.external_id,
                    external_entity_key=identity.external_key,
                    projection_hash=ViewerManagedState.from_projection(projection).projection_hash,
                    error=None,
                    last_synced_at=datetime.now(UTC),
                )
                external_ids[snapshot.identifier] = identity.external_id
            records.append(await self._viewer_repository.save_sync_record(persisted_record))
        succeeded = sum(record.sync_status is SyncStatus.SYNCED for record in records)
        failed = len(records) - succeeded
        return await self._viewer_repository.save_operation(
            replace(
                operation,
                status=self._completion_status(len(records), succeeded),
                finished_at=datetime.now(UTC),
                total_items=len(records),
                succeeded_items=succeeded,
                failed_items=failed,
                error="Some Viewer projections could not be published." if failed else None,
            )
        )

    async def _check_drift(self, operation: ViewerOperation) -> ViewerOperation:
        """Check the selected external Viewer for drift in its project projections."""
        offset = 0
        checked = 0
        failed = 0
        while True:
            operation = await self._heartbeat(operation)
            pagination = PaginationParams(offset=offset, limit=MAX_PAGE_LIMIT)
            page = await self._viewer_repository.find_sync_records_page_by_project(
                operation.project_key, pagination, operation.viewer_type
            )
            page_checked, page_failed = await self._check_drift_page(page.items)
            checked += page_checked
            failed += page_failed
            offset += len(page.items)
            if offset >= page.total:
                return await self._viewer_repository.save_operation(
                    replace(
                        operation,
                        status=self._completion_status(page.total, checked),
                        finished_at=datetime.now(UTC),
                        total_items=page.total,
                        succeeded_items=checked,
                        failed_items=failed,
                        error="Some Viewer drift checks could not be completed."
                        if failed
                        else None,
                    )
                )

    async def _check_drift_page(self, records: tuple[ViewerSyncRecord, ...]) -> tuple[int, int]:
        checked = 0
        failed = 0
        for record in records:
            try:
                projection = await self._projection_for_drift(record)
                observation = await self._viewer_drift_detector.check_drift(projection)
            except Exception as error:
                failed += 1
                await self._viewer_repository.save_sync_record(
                    replace(
                        record,
                        sync_status=SyncStatus.ERROR,
                        error=self._sync_error(error),
                    )
                )
                continue
            checked += 1
            await self._persist_drift_observation(record, observation)
            await self._viewer_repository.save_sync_record(
                replace(
                    record,
                    sync_status=(
                        SyncStatus.DRIFT_DETECTED if observation is not None else SyncStatus.SYNCED
                    ),
                    error=None,
                    last_checked_at=datetime.now(UTC),
                )
            )
        return checked, failed

    async def _projection_for_drift(self, record: ViewerSyncRecord) -> ViewerProjection:
        snapshot = await self._snapshot_for_record(record)
        if snapshot is None:
            raise ViewerProjectionIntegrityException("published Viewer snapshot is unavailable")
        snapshots_by_id = {snapshot.identifier: snapshot}
        if isinstance(snapshot, TestPlan):
            for test_set_id in snapshot.test_set_ids:
                test_set = await self._test_set_repository.find_by_id(test_set_id)
                if test_set is not None:
                    snapshots_by_id[test_set.identifier] = test_set
        return ViewerProjectionBuilder.build(
            record,
            snapshot,
            snapshots_by_id,
            await self._external_ids_for_project(record.project_key, record.viewer_type),
        )

    async def _snapshot_for_record(self, record: ViewerSyncRecord) -> ViewerSnapshot | None:
        repositories = {
            ViewerEntityType.TEST_CASE: self._test_case_repository,
            ViewerEntityType.PRECONDITION: self._precondition_repository,
            ViewerEntityType.TEST_SET: self._test_set_repository,
            ViewerEntityType.TEST_PLAN: self._test_plan_repository,
        }
        return await repositories[record.entity_type].find_by_id(record.projected_version_id)

    async def _external_ids_for_project(
        self, project_key: str, viewer_type: ViewerType
    ) -> dict[UUID, str]:
        offset = 0
        external_ids: dict[UUID, str] = {}
        while True:
            page = await self._viewer_repository.find_sync_records_page_by_project(
                project_key, PaginationParams(offset=offset, limit=MAX_PAGE_LIMIT), viewer_type
            )
            external_ids.update(
                {
                    record.projected_version_id: record.external_entity_id
                    for record in page.items
                    if record.sync_status is SyncStatus.SYNCED
                    and record.external_entity_id is not None
                }
            )
            offset += len(page.items)
            if offset >= page.total:
                return external_ids

    @staticmethod
    def _completion_status(total: int, succeeded: int) -> ViewerOperationStatus:
        if succeeded == total:
            return ViewerOperationStatus.SUCCEEDED
        if succeeded == 0:
            return ViewerOperationStatus.FAILED
        return ViewerOperationStatus.PARTIALLY_SUCCEEDED

    @staticmethod
    def _sync_error(error: Exception) -> str:
        return f"{type(error).__name__}: {error}"[:500]

    async def _persist_drift_observation(
        self, record: ViewerSyncRecord, observation: DriftObservation | None
    ) -> None:
        if observation is None or record.sync_status is SyncStatus.DRIFT_DETECTED:
            return
        await self._viewer_repository.save_drift_event(
            DriftEvent(
                identifier=uuid4(),
                project_key=record.project_key,
                sync_record_id=record.identifier,
                projected_version_id=record.projected_version_id,
                detected_at=datetime.now(UTC),
                drift_type=observation.drift_type,
                notification_status=NotificationStatus.PENDING,
                details=observation.details,
            )
        )

    async def _active_snapshots(self, project_key: str):
        test_cases = await self._all_active(self._test_case_repository, project_key)
        preconditions = await self._all_active(self._precondition_repository, project_key)
        test_sets = await self._all_active(self._test_set_repository, project_key)
        test_plans = await self._all_active(self._test_plan_repository, project_key)
        return (
            tuple((ViewerEntityType.PRECONDITION, item) for item in preconditions)
            + tuple((ViewerEntityType.TEST_CASE, item) for item in test_cases)
            + tuple((ViewerEntityType.TEST_SET, item) for item in test_sets)
            + tuple((ViewerEntityType.TEST_PLAN, item) for item in test_plans)
        )

    async def _heartbeat(self, operation: ViewerOperation) -> ViewerOperation:
        return await self._viewer_repository.save_operation(
            replace(operation, started_at=datetime.now(UTC))
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
