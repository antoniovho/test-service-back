from datetime import UTC, datetime
from uuid import uuid4

import pytest

from test_service.domain.application.services.viewer_projection_builder import (
    ViewerProjectionBuilder,
)
from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.exceptions.viewer_projection_integrity_exception import (
    ViewerProjectionIntegrityException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.model.viewer.records import (
    SyncStatus,
    ViewerEntityType,
    ViewerSyncRecord,
    ViewerType,
)


def _record(entity_type: ViewerEntityType) -> ViewerSyncRecord:
    return ViewerSyncRecord(
        identifier=uuid4(),
        project_key="SHOP",
        entity_type=entity_type,
        entity_key="projection",
        entity_version=1,
        projected_version_id=uuid4(),
        viewer_type=ViewerType.XRAY,
        external_entity_key="projection",
        sync_status=SyncStatus.PENDING,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestViewerProjectionBuilder:
    def test_when_test_set_dependency_is_not_synchronized_expect_integrity_exception(self) -> None:
        test_set = TestSet(
            identifier=uuid4(),
            project_key="SHOP",
            set_key="checkout",
            version=1,
            name="Checkout",
            items=(uuid4(),),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="author@example.test",
            status=VersionStatus.ACTIVE,
        )

        with pytest.raises(ViewerProjectionIntegrityException) as error:
            ViewerProjectionBuilder.build(_record(ViewerEntityType.TEST_SET), test_set, {}, {})

        assert error.value.code == "VIEWER_PROJECTION_INVALID"

    def test_when_test_plan_references_unavailable_set_expect_integrity_exception(self) -> None:
        test_plan = TestPlan(
            identifier=uuid4(),
            project_key="SHOP",
            plan_key="release",
            version=1,
            name="Release",
            execution_mode=ExecutionMode.SEQUENTIAL,
            timeout_seconds=60,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="author@example.test",
            test_set_ids=(uuid4(),),
            status=VersionStatus.ACTIVE,
        )

        with pytest.raises(ViewerProjectionIntegrityException) as error:
            ViewerProjectionBuilder.build(_record(ViewerEntityType.TEST_PLAN), test_plan, {}, {})

        assert error.value.code == "VIEWER_PROJECTION_INVALID"
