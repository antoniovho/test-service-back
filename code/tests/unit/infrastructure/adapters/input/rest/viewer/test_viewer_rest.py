from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from test_service_server.models.sort_order import SortOrder as ApiSortOrder
from test_service_server.models.viewer_operation_request import ViewerOperationRequest
from test_service_server.models.viewer_type import ViewerType as ApiViewerType

from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import (
    DriftEvent,
    DriftType,
    NotificationStatus,
    SyncStatus,
    ViewerEntityType,
    ViewerOperation,
    ViewerOperationStatus,
    ViewerOperationType,
    ViewerSyncRecord,
    ViewerType,
)
from test_service.infrastructure.adapters.input.rest.viewer import viewer_integration_controller
from test_service.infrastructure.adapters.input.rest.viewer.viewer_integration_controller import (
    ViewerIntegrationController,
)
from test_service.infrastructure.adapters.input.rest.viewer.viewer_mapper import ViewerMapper


def _controller() -> ViewerIntegrationController:
    controller = ViewerIntegrationController.__new__(ViewerIntegrationController)
    controller.__dict__.update(
        _publish=SimpleNamespace(execute=AsyncMock(return_value=_operation())),
        _get_project=SimpleNamespace(
            execute=AsyncMock(return_value=SimpleNamespace(key="IAG", name="AI Gateway"))
        ),
        _check_drift=SimpleNamespace(execute=AsyncMock(return_value=_operation())),
        _list_sync=SimpleNamespace(execute=AsyncMock(return_value=Page((), 0))),
        _list_project_sync=SimpleNamespace(execute=AsyncMock(return_value=Page((), 0))),
        _list_drift=SimpleNamespace(execute=AsyncMock(return_value=Page((), 0))),
        _list_project_drift=SimpleNamespace(execute=AsyncMock(return_value=Page((), 0))),
        _list_operations=SimpleNamespace(execute=AsyncMock(return_value=Page((), 0))),
        _list_project_operations=SimpleNamespace(execute=AsyncMock(return_value=Page((), 0))),
        _get_operation=SimpleNamespace(execute=AsyncMock(return_value=_operation())),
    )
    return controller


def _operation() -> ViewerOperation:
    return ViewerOperation(
        identifier=uuid4(),
        project_key="IAG",
        viewer_type=ViewerType.XRAY,
        operation_type=ViewerOperationType.PUBLICATION,
        status=ViewerOperationStatus.PENDING,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestViewerRest:
    def test_when_creating_controller_expect_all_use_cases_injected(self, monkeypatch) -> None:
        injector = SimpleNamespace(inject=MagicMock(side_effect=[object() for _ in range(10)]))
        monkeypatch.setattr(viewer_integration_controller, "get_injector", lambda: injector)

        controller = ViewerIntegrationController()

        assert injector.inject.call_count == 10
        assert controller._publish is not None
        assert controller._list_project_drift is not None

    async def test_when_checking_drift_expect_project_name_in_response(self) -> None:
        controller = _controller()
        controller._check_drift.execute = AsyncMock(return_value=_operation())

        response = await controller.check_viewer_drift(
            "IAG", ViewerOperationRequest(viewerType="XRAY")
        )

        assert response.project.name == "AI Gateway"
        assert controller._check_drift.execute.await_args.args[0].viewer_type is ViewerType.XRAY

    async def test_when_listing_viewer_data_expect_project_names_resolved_once_per_project(
        self,
    ) -> None:
        record = ViewerSyncRecord(
            identifier=uuid4(),
            project_key="IAG",
            entity_type=ViewerEntityType.TEST_CASE,
            entity_key="LOGIN",
            projected_version_id=uuid4(),
            viewer_type=ViewerType.XRAY,
            external_entity_key="LOGIN",
            sync_status=SyncStatus.SYNCED,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        event = DriftEvent(
            identifier=uuid4(),
            project_key="IAG",
            sync_record_id=record.identifier,
            projected_version_id=record.projected_version_id,
            detected_at=datetime(2026, 1, 2, tzinfo=UTC),
            drift_type=DriftType.MISSING,
            notification_status=NotificationStatus.PENDING,
        )
        controller = _controller()
        controller._list_sync.execute = AsyncMock(return_value=Page((record,), 1))
        controller._list_project_sync.execute = AsyncMock(return_value=Page((record,), 1))
        controller._list_drift.execute = AsyncMock(return_value=Page((event,), 1))
        controller._list_project_drift.execute = AsyncMock(return_value=Page((event,), 1))

        sync = await controller.list_viewer_sync_records(None, 0, 20, None, None)
        project_sync = await controller.list_project_viewer_sync_records(
            "IAG", None, 0, 20, None, None
        )
        drift = await controller.list_viewer_drift_events(None, 0, 20, None, None)
        project_drift = await controller.list_project_viewer_drift_events(
            "IAG", None, 0, 20, None, None
        )

        assert sync.data[0].project.name == "AI Gateway"
        assert project_sync.data[0].project.name == "AI Gateway"
        assert drift.data[0].project.name == "AI Gateway"
        assert project_drift.data[0].project.name == "AI Gateway"

    async def test_when_publishing_viewer_projection_expect_project_name_in_response(self) -> None:
        controller = _controller()
        controller._publish.execute = AsyncMock(return_value=_operation())

        response = await controller.publish_viewer_projection(
            "IAG", ViewerOperationRequest(viewerType="XRAY")
        )

        assert response.project.key == "IAG"
        assert response.project.name == "AI Gateway"

    def test_when_mapping_sync_record_expect_project_reference_with_name(self) -> None:
        record = ViewerSyncRecord(
            identifier=uuid4(),
            project_key="IAG",
            entity_type=ViewerEntityType.TEST_CASE,
            entity_key="LOGIN",
            projected_version_id=uuid4(),
            viewer_type=ViewerType.XRAY,
            external_entity_key="LOGIN",
            sync_status=SyncStatus.SYNCED,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        api_record = ViewerMapper.sync_record_to_api(record, "AI Gateway")

        assert api_record.project.key == "IAG"
        assert api_record.project.name == "AI Gateway"

    def test_when_mapping_viewer_operation_request_expect_viewer_type_in_commands(self) -> None:
        request = ViewerOperationRequest(viewerType="XRAY")

        publish = ViewerMapper.to_publish_command("IAG", request)
        drift = ViewerMapper.to_check_drift_command("IAG", request)

        assert publish.project_key == "IAG"
        assert publish.viewer_type is ViewerType.XRAY
        assert drift.viewer_type is ViewerType.XRAY

    def test_when_mapping_viewer_type_filter_expect_domain_query_filter(self) -> None:
        pagination = ViewerMapper.to_pagination(0, 10, "createdAt", ApiSortOrder.ASC)

        query = ViewerMapper.to_list_project_sync_records_query(
            "IAG", pagination, ApiViewerType.XRAY
        )

        assert query.project_key == "IAG"
        assert query.viewer_type is ViewerType.XRAY

    async def test_when_viewer_endpoints_receive_contract_inputs_expect_use_case_requests(
        self,
    ) -> None:
        controller = _controller()
        request = ViewerOperationRequest(viewerType="XRAY")

        publication = await controller.publish_viewer_projection("IAG", request)
        records = await controller.list_viewer_sync_records(
            ApiViewerType.XRAY, 0, 10, "createdAt", ApiSortOrder.ASC
        )

        assert publication.status == "PENDING"
        assert records.pagination.total == 0
        assert controller._publish.execute.await_args.args[0].viewer_type is ViewerType.XRAY
        assert controller._list_sync.execute.await_args.args[0].viewer_type is ViewerType.XRAY

    async def test_when_listing_and_getting_operations_expect_operation_responses(self) -> None:
        operation = _operation()
        controller = _controller()
        controller._list_operations.execute = AsyncMock(return_value=Page((operation,), 1))
        controller._list_project_operations.execute = AsyncMock(return_value=Page((operation,), 1))
        controller._get_operation.execute = AsyncMock(return_value=operation)

        global_page = await controller.list_viewer_operations(None, 0, 20, None, None)
        project_page = await controller.list_project_viewer_operations(
            "IAG", None, 0, 20, None, None
        )
        response = await controller.get_project_viewer_operation("IAG", operation.identifier)

        assert global_page.data[0].id == operation.identifier
        assert project_page.data[0].project.key == "IAG"
        assert response.status == "PENDING"
