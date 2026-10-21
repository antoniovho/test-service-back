from datetime import UTC, datetime
from uuid import uuid4

import pytest

from test_service.domain.application.services.viewer_projection_builder import (
    ViewerProjectionBuilder,
)
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.authoring.test_case import Priority, TestCase, TestLevel, TestType
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
    def test_when_building_precondition_expect_title_description_and_json_definition(self) -> None:
        precondition = Precondition(
            identifier=uuid4(),
            project_key="KAN",
            precondition_key="LITELLM_PROXY_READY",
            version=1,
            name="LiteLLM Proxy readiness endpoint reports a healthy service",
            description="Checks the unauthenticated readiness probe documented by LiteLLM.",
            validation_definition=Definition(
                {},
                (
                    Action(
                        "proxyReadiness",
                        "HTTP",
                        {"method": "GET", "url": "{{gateway_base_url}}/health/readiness"},
                    ),
                ),
            ),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="corpus-import",
            status=VersionStatus.ACTIVE,
            metadata={"labels": ["litellm", "readiness", "litellm", "", 1]},
        )

        projection = ViewerProjectionBuilder.build(
            _record(ViewerEntityType.PRECONDITION), precondition, {}, {}
        )

        assert projection.summary == (
            "LITELLM_PROXY_READY v1 - LiteLLM Proxy readiness endpoint reports a healthy service"
        )
        assert (
            projection.description
            == "Checks the unauthenticated readiness probe documented by LiteLLM."
        )
        assert projection.definition == (
            "[\n"
            "  {\n"
            '    "configuration": {\n'
            '      "method": "GET",\n'
            '      "url": "{{gateway_base_url}}/health/readiness"\n'
            "    },\n"
            '    "id": "proxyReadiness",\n'
            '    "type": "HTTP"\n'
            "  }\n"
            "]"
        )
        assert projection.labels == ("litellm", "readiness")

    def test_when_building_test_case_expect_business_context_in_description(self) -> None:
        test_case = TestCase(
            identifier=uuid4(),
            project_key="KAN",
            test_key="GW-SMK-003",
            version=1,
            name="Gateway returns a basic chat completion",
            summary="Gateway returns a basic chat completion",
            objective=(
                "Verify a minimal valid chat request returns an OpenAI-compatible completion."
            ),
            test_type=TestType.AUTOMATED,
            test_level=TestLevel.INTEGRATION,
            priority=Priority.MEDIUM,
            definition=Definition({}, (Action("createBasicChatCompletion", "HTTP", {}),)),
            timeout_seconds=60,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="corpus-import",
            status=VersionStatus.ACTIVE,
            metadata={
                "labels": ["litellm", "smoke"],
                "objective": "Duplicate objective",
                "source": "https://example.test",
            },
        )

        projection = ViewerProjectionBuilder.build(
            _record(ViewerEntityType.TEST_CASE), test_case, {}, {}
        )

        assert projection.summary == "GW-SMK-003 v1 - Gateway returns a basic chat completion"
        assert projection.description == (
            "**Summary**\nGateway returns a basic chat completion\n\n"
            "**Objective**\nVerify a minimal valid chat request returns an OpenAI-compatible "
            "completion.\n\n**Classification**\n- **Type:** AUTOMATED\n- **Level:** INTEGRATION\n"
            "- **Priority:** MEDIUM\n- **Timeout:** 60 seconds\n\n**Source**\n"
            "- **Test key:** GW-SMK-003\n- **Version:** 1\n\n**Metadata**\n```json\n"
            '{\n  "labels": [\n    "litellm",\n    "smoke"\n  ],\n'
            '  "source": "https://example.test"\n}\n```'
        )
        assert projection.labels == ("litellm", "smoke")

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
