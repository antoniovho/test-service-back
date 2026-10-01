"""Shared projection and project access behavior for Viewer use cases."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.application.services.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import MAX_PAGE_LIMIT, PaginationParams
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.model.viewer.records import (
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
        for entity_type, entity_key, identifier in snapshots:
            record = ViewerSyncRecord(
                identifier=uuid4(),
                project_key=operation.project_key,
                entity_type=entity_type,
                entity_key=entity_key,
                projected_version_id=identifier,
                viewer_type=operation.viewer_type,
                external_entity_key=entity_key,
                sync_status=SyncStatus.PENDING,
                created_at=datetime.now(UTC),
                operation_id=operation.identifier,
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
            pagination = PaginationParams(offset=offset, limit=MAX_PAGE_LIMIT)
            page = await self._viewer_repository.find_sync_records_page_by_project(
                operation.project_key, pagination, operation.viewer_type
            )
            for record in page.items:
                try:
                    await self._viewer_drift_detector.check_drift(record)
                except Exception:
                    failed += 1
                    await self._viewer_repository.save_sync_record(
                        replace(record, sync_status=SyncStatus.ERROR)
                    )
                else:
                    checked += 1
                    await self._viewer_repository.save_sync_record(
                        replace(record, last_checked_at=datetime.now(UTC))
                    )
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

    @staticmethod
    def _completion_status(total: int, succeeded: int) -> ViewerOperationStatus:
        if succeeded == total:
            return ViewerOperationStatus.SUCCEEDED
        if succeeded == 0:
            return ViewerOperationStatus.FAILED
        return ViewerOperationStatus.PARTIALLY_SUCCEEDED

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
