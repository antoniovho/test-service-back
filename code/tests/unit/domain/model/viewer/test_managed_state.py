from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.model.viewer.managed_state import ViewerManagedState
from test_service.domain.model.viewer.projection import ViewerProjection, ViewerProjectionStep
from test_service.domain.model.viewer.records import (
    SyncStatus,
    ViewerEntityType,
    ViewerSyncRecord,
    ViewerType,
)


def _projection(
    entity_type: ViewerEntityType = ViewerEntityType.TEST_CASE,
    *,
    description: str | None = None,
    steps: tuple[ViewerProjectionStep, ...] = (),
    precondition_external_ids: tuple[str, ...] = (),
    test_external_ids: tuple[str, ...] = (),
) -> ViewerProjection:
    return ViewerProjection(
        record=ViewerSyncRecord(
            identifier=uuid4(),
            project_key="SHOP",
            entity_type=entity_type,
            entity_key="checkout",
            entity_version=1,
            projected_version_id=uuid4(),
            viewer_type=ViewerType.XRAY,
            external_entity_key="checkout",
            sync_status=SyncStatus.PENDING,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        summary="Checkout succeeds",
        description=description,
        steps=steps,
        precondition_external_ids=precondition_external_ids,
        test_external_ids=test_external_ids,
    )


class TestViewerManagedState:
    def test_when_test_steps_differ_only_by_line_endings_and_whitespace_expect_same_hash(
        self,
    ) -> None:
        first = _projection(
            steps=(ViewerProjectionStep(" submit\r\n order ", " { } ", " 201 \r\n Created "),)
        )
        second = _projection(steps=(ViewerProjectionStep("submit\norder", "{ }", "201\nCreated"),))

        first_state = ViewerManagedState.from_projection(first)
        second_state = ViewerManagedState.from_projection(second)

        assert first_state.projection_hash == second_state.projection_hash

    def test_when_relationship_order_differs_expect_same_hash(self) -> None:
        first = _projection(precondition_external_ids=("10002", "10001", "10002"))
        second = _projection(precondition_external_ids=("10001", "10002"))

        first_state = ViewerManagedState.from_projection(first)
        second_state = ViewerManagedState.from_projection(second)

        assert first_state.projection_hash == second_state.projection_hash

    def test_when_step_order_differs_expect_steps_difference(self) -> None:
        expected = ViewerManagedState.from_projection(
            _projection(
                steps=(
                    ViewerProjectionStep("first", None, None),
                    ViewerProjectionStep("second", None, None),
                )
            )
        )
        actual = ViewerManagedState.from_projection(
            _projection(
                steps=(
                    ViewerProjectionStep("second", None, None),
                    ViewerProjectionStep("first", None, None),
                )
            )
        )

        differences = expected.differing_fields(actual)

        assert differences == ("steps",)

    def test_when_precondition_definition_differs_expect_safe_field_name(self) -> None:
        expected = ViewerManagedState.from_projection(
            _projection(ViewerEntityType.PRECONDITION, description="The service is available.")
        )
        actual = ViewerManagedState.from_projection(
            _projection(ViewerEntityType.PRECONDITION, description="Sensitive remote text")
        )

        differences = expected.differing_fields(actual)

        assert differences == ("definition",)
