"""Object mothers for execution and Test Case tests."""

from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import UUID, uuid4

from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import (
    PreconditionReference,
    Priority,
    TestCase,
    TestLevel,
    TestType,
)
from test_service.domain.model.execution.execution import Execution, ExecutionStatus, TriggerType
from test_service.domain.model.lifecycle import VersionStatus

_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def a_test_case(
    *,
    identifier: UUID | None = None,
    project_key: str = "IAG",
    test_key: str = "checkout",
    version: int = 1,
    name: str = "Checkout",
    summary: str = "Checks checkout",
    objective: str = "Complete checkout",
    test_type: TestType = TestType.AUTOMATED,
    test_level: TestLevel = TestLevel.FUNCTIONAL,
    priority: Priority = Priority.HIGH,
    definition: Definition | None = None,
    variables: Mapping[str, str] | None = None,
    timeout_seconds: int = 60,
    created_at: datetime = _CREATED_AT,
    created_by: str = "author@example.test",
    preconditions: tuple[PreconditionReference, ...] = (),
    status: VersionStatus = VersionStatus.ACTIVE,
) -> TestCase:
    """Return a valid automated Test Case with only scenario fields overridden."""
    if definition is None:
        definition = Definition(
            variables=variables or {},
            actions=(Action("request", "HTTP", {"url": "https://example.test"}),),
        )
    return TestCase(
        identifier=identifier or uuid4(),
        project_key=project_key,
        test_key=test_key,
        version=version,
        name=name,
        summary=summary,
        objective=objective,
        test_type=test_type,
        test_level=test_level,
        priority=priority,
        definition=definition,
        timeout_seconds=timeout_seconds,
        created_at=created_at,
        created_by=created_by,
        preconditions=preconditions,
        status=status,
    )


def an_execution(
    *,
    identifier: UUID | None = None,
    project_key: str = "IAG",
    test_plan_id: UUID | None = None,
    environment_id: UUID | None = None,
    trigger_type: TriggerType = TriggerType.API,
    created_at: datetime = _CREATED_AT,
    test_case_ids: tuple[UUID, ...] = (),
    environment_snapshot: Mapping[str, object] | None = None,
    status: ExecutionStatus = ExecutionStatus.CREATED,
    triggered_by: str | None = None,
    runner_identifier: str | None = None,
    runner_version: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    duration_ms: int | None = None,
) -> Execution:
    """Return a valid Execution aggregate with explicit lifecycle overrides."""
    return Execution(
        identifier=identifier or uuid4(),
        project_key=project_key,
        test_plan_id=test_plan_id or uuid4(),
        environment_id=environment_id or uuid4(),
        trigger_type=trigger_type,
        created_at=created_at,
        test_case_ids=test_case_ids,
        environment_snapshot=environment_snapshot,
        status=status,
        triggered_by=triggered_by,
        runner_identifier=runner_identifier,
        runner_version=runner_version,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
    )
