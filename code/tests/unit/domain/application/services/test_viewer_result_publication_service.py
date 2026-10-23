import json
import logging
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from test_service.config import ViewerSettings
from test_service.domain.application.queries.pagination import Page
from test_service.domain.application.services.viewer_result_publication_service import (
    ViewerResultPublicationService,
)
from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.exceptions.permanent_viewer_result_publication_exception import (
    PermanentViewerResultPublicationError,
)
from test_service.domain.model.execution.environment import Environment, EnvironmentStatus
from test_service.domain.model.execution.execution import (
    ActionResult,
    ArtifactType,
    ExecutionStatus,
    ResultStatus,
    StorageType,
    TestResult,
    TestResultArtifact,
)
from test_service.domain.model.viewer.execution_result_projection import (
    ViewerExecutionResultIdentity,
)
from test_service.domain.model.viewer.execution_results import (
    ViewerResultPublication,
    ViewerResultPublicationStatus,
)
from test_service.domain.model.viewer.records import (
    SyncStatus,
    ViewerEntityType,
    ViewerSyncRecord,
    ViewerType,
)
from tests.mothers.execution_mother import a_test_case, an_execution

_CREATED_AT = datetime(2026, 1, 1, 10, tzinfo=UTC)
_FINISHED_AT = datetime(2026, 1, 1, 10, 0, 1, tzinfo=UTC)


class _Executions:
    def __init__(self, execution) -> None:
        self._execution = execution

    async def find_execution(self, _):
        return self._execution


class _Results:
    def __init__(
        self,
        result: TestResult,
        actions: tuple[ActionResult, ...] = (),
        artifacts: tuple[TestResultArtifact, ...] = (),
    ) -> None:
        self._result = result
        self._actions = actions
        self._artifacts = artifacts

    async def find_results_page(self, _, __):
        return Page((self._result,), 1)

    async def find_actions_page(self, _, __):
        return Page(self._actions, len(self._actions))

    async def find_artifacts_page(self, _, __):
        return Page(self._artifacts, len(self._artifacts))


class _Environments:
    def __init__(self, environment: Environment) -> None:
        self._environment = environment

    async def find_by_id(self, _):
        return self._environment


class _TestCases:
    def __init__(self, test_case) -> None:
        self._test_case = test_case

    async def find_by_id(self, _):
        return self._test_case


class _TestPlans:
    def __init__(self, test_plan: TestPlan) -> None:
        self._test_plan = test_plan

    async def find_by_id(self, _):
        return self._test_plan


class _ViewerRecords:
    def __init__(self, records: dict[ViewerEntityType, ViewerSyncRecord | None]) -> None:
        self._records = records

    async def find_sync_record(self, project_key, entity_type, *args):
        return self._records.get(entity_type)


class _Publications:
    def __init__(self, publication: ViewerResultPublication) -> None:
        self._publication = publication
        self.saved: list[ViewerResultPublication] = []
        self.completions = []

    async def transition_execution_and_enqueue_result_publication(
        self, execution, expected_statuses, viewer_type
    ):
        self.completions.append((execution, expected_statuses, viewer_type))
        return execution

    async def claim_next_result_publication(self):
        return self._publication

    async def save_result_publication(self, publication):
        self.saved.append(publication)
        return publication


class _Publisher:
    def __init__(self) -> None:
        self.projections = []

    @property
    def viewer_type(self) -> ViewerType:
        return ViewerType.XRAY

    async def publish_execution_result(self, projection):
        self.projections.append(projection)
        return ViewerExecutionResultIdentity(
            execution_id="20001",
            execution_key="IAG-9",
            test_run_ids={projection.test_runs[0].test_result_id: "30001"},
        )


class _PermanentFailurePublisher(_Publisher):
    async def publish_execution_result(self, projection):
        raise PermanentViewerResultPublicationError("Authorization: Bearer provider-secret")


class TestViewerResultPublicationService:
    async def test_when_completing_execution_expect_publisher_viewer_type(self) -> None:
        service, publications, _, _ = self._service(record=self._sync_record())
        execution = (
            an_execution(created_at=_CREATED_AT)
            .start(_CREATED_AT)
            .complete(ExecutionStatus.FAILED, _FINISHED_AT)
        )

        result = await service.complete_execution(execution, (ExecutionStatus.RUNNING,))

        assert result is execution
        assert publications.completions == [
            (execution, (ExecutionStatus.RUNNING,), ViewerType.XRAY)
        ]

    async def test_when_test_identity_is_unsynchronized_expect_retry_wait(self, caplog) -> None:
        service, publications, _, test_result = self._service(record=None)
        caplog.set_level(logging.WARNING)

        result = await service.process_next_publication()

        assert result is not None
        assert result.status is ViewerResultPublicationStatus.RETRY_WAIT
        assert "not synchronized" in (result.error or "")
        assert str(publications._publication.identifier) in (result.error or "")
        assert str(publications._publication.execution_id) in (result.error or "")
        assert str(test_result.identifier) in (result.error or "")
        assert str(test_result.test_case_id) in (result.error or "")
        assert publications.saved == [result]
        assert f"Viewer result publication '{result.identifier}'" in caplog.messages[0]
        assert "will retry" in caplog.messages[0]

    async def test_when_result_is_resolved_expect_safe_projection_and_persisted_identity(
        self, caplog
    ) -> None:
        caplog.set_level(logging.INFO)
        service, publications, publisher, test_result = self._service(
            record=self._sync_record(),
            error_message=("Authorization: Bearer secret-value failed"),
        )

        result = await service.process_next_publication()

        assert result is not None
        assert result.status is ViewerResultPublicationStatus.SUCCEEDED
        assert result.external_execution_id == "20001"
        projection = publisher.projections[0]
        assert projection.environment_name == "Integration"
        assert projection.external_test_plan_id == "20001"
        assert projection.test_runs[0].status is ResultStatus.FAILED
        assert "secret-value" not in (projection.test_runs[0].comment or "")
        assert "[REDACTED]" in (projection.test_runs[0].comment or "")
        assert publications.saved == [result]
        assert projection.test_runs[0].test_result_id == test_result.identifier
        assert f"Viewer result publication '{result.identifier}'" in caplog.messages[0]
        assert "succeeded as external execution '20001' ('IAG-9')" in caplog.messages[0]

    async def test_when_result_has_log_artifact_expect_safe_viewer_evidence(self) -> None:
        service, _, publisher, test_result = self._service(
            record=self._sync_record(), artifact_contents=("token=provider-secret execution trace",)
        )

        await service.process_next_publication()

        evidence = publisher.projections[0].test_runs[0].evidence
        assert len(evidence) == 1
        assert evidence[0].mime_type == "text/plain"
        assert "provider-secret" not in evidence[0].content
        assert "[REDACTED]" in evidence[0].content
        assert str(test_result.identifier) in evidence[0].filename

    @pytest.mark.parametrize(
        ("execution_status", "result_status"),
        [
            (ExecutionStatus.PASSED, ResultStatus.PASSED),
            (ExecutionStatus.FAILED, ResultStatus.FAILED),
            (ExecutionStatus.FAILED, ResultStatus.ERROR),
        ],
        ids=["passed", "failed", "error"],
    )
    async def test_when_result_has_action_actual_expect_step_and_global_evidence_separated(
        self, execution_status: ExecutionStatus, result_status: ResultStatus
    ) -> None:
        service, _, publisher, test_result = self._service(
            record=self._sync_record(),
            execution_status=execution_status,
            result_status=result_status,
        )
        action = ActionResult(
            identifier=uuid4(),
            test_result_id=test_result.identifier,
            action_id="request",
            action_type="HTTP",
            status=result_status,
            created_at=_CREATED_AT,
            actual={"response": {"statusCode": 200}},
        )
        precondition_summary = ActionResult(
            identifier=uuid4(),
            test_result_id=test_result.identifier,
            action_id="precondition:ready",
            action_type="PRECONDITION",
            status=ResultStatus.PASSED,
            created_at=_CREATED_AT,
            actual={"actionCount": 1},
        )
        precondition_action = ActionResult(
            identifier=uuid4(),
            test_result_id=test_result.identifier,
            action_id="precondition:ready:check",
            action_type="HTTP",
            status=ResultStatus.PASSED,
            created_at=_CREATED_AT,
            actual={"authorization": "provider-secret", "ready": True},
        )
        step_artifact = TestResultArtifact(
            identifier=uuid4(),
            test_result_id=test_result.identifier,
            action_result_id=action.identifier,
            artifact_type=ArtifactType.LOG,
            storage_type=StorageType.DB,
            created_at=_FINISHED_AT,
            content="action trace",
        )
        precondition_artifact = TestResultArtifact(
            identifier=uuid4(),
            test_result_id=test_result.identifier,
            action_result_id=precondition_action.identifier,
            artifact_type=ArtifactType.LOG,
            storage_type=StorageType.DB,
            created_at=_FINISHED_AT,
            content="precondition trace",
        )
        service._results = _Results(
            test_result,
            (action, precondition_summary, precondition_action),
            (step_artifact, precondition_artifact),
        )

        await service.process_next_publication()

        test_run = publisher.projections[0].test_runs[0]
        action_actual = json.dumps(
            {
                "action": {"id": "request", "status": result_status.value, "type": "HTTP"},
                "actual": {"response": {"statusCode": 200}},
            },
            sort_keys=True,
        )
        precondition_actual = json.dumps(
            {
                "action": {
                    "id": "precondition:ready:check",
                    "status": "PASSED",
                    "type": "HTTP",
                },
                "actual": {"authorization": "[REDACTED]", "ready": True},
            },
            sort_keys=True,
        )
        assert [(step.action_id, step.status) for step in test_run.steps] == [
            ("request", result_status)
        ]
        assert [evidence.content for evidence in test_run.steps[0].evidence] == [
            action_actual,
            "action trace",
        ]
        assert [evidence.content for evidence in test_run.evidence] == [
            precondition_actual,
            "precondition trace",
        ]
        assert all("actionCount" not in evidence.content for evidence in test_run.evidence)
        assert test_run.steps[0].evidence[0].filename.endswith("request-HTTP-actual.json")

    async def test_when_blocked_result_has_precondition_actual_expect_test_run_evidence(
        self,
    ) -> None:
        service, _, publisher, test_result = self._service(
            record=self._sync_record(), result_status=ResultStatus.BLOCKED
        )
        precondition_summary = ActionResult(
            identifier=uuid4(),
            test_result_id=test_result.identifier,
            action_id="precondition:ready",
            action_type="PRECONDITION",
            status=ResultStatus.ERROR,
            created_at=_CREATED_AT,
            actual={"actionCount": 1},
        )
        precondition_action = ActionResult(
            identifier=uuid4(),
            test_result_id=test_result.identifier,
            action_id="precondition:ready:check",
            action_type="HTTP",
            status=ResultStatus.ERROR,
            created_at=_CREATED_AT,
            actual={"ready": False, "statusCode": 503},
        )
        service._results = _Results(test_result, (precondition_summary, precondition_action))

        await service.process_next_publication()

        test_run = publisher.projections[0].test_runs[0]
        precondition_actual = json.dumps(
            {
                "action": {
                    "id": "precondition:ready:check",
                    "status": "ERROR",
                    "type": "HTTP",
                },
                "actual": {"ready": False, "statusCode": 503},
            },
            sort_keys=True,
        )
        assert test_run.status is ResultStatus.BLOCKED
        assert [evidence.content for evidence in test_run.evidence] == [precondition_actual]

    async def test_when_result_publication_is_permanently_rejected_expect_safe_error_log(
        self, caplog
    ) -> None:
        service, publications, _, _ = self._service(
            record=self._sync_record(), publisher=_PermanentFailurePublisher()
        )
        caplog.set_level(logging.ERROR)

        result = await service.process_next_publication()

        assert result is not None
        assert result.status is ViewerResultPublicationStatus.FAILED_PERMANENT
        assert "provider-secret" not in caplog.messages[0]
        assert "[REDACTED]" in caplog.messages[0]
        assert "failed permanently" in caplog.messages[0]
        assert publications.saved == [result]

    async def test_when_execution_is_cancelled_expect_skipped_result_is_aborted(self) -> None:
        service, _, publisher, _ = self._service(
            record=self._sync_record(),
            execution_status=ExecutionStatus.CANCELLED,
            result_status=ResultStatus.SKIPPED,
        )

        await service.process_next_publication()

        projection = publisher.projections[0]
        assert projection.execution_status is ExecutionStatus.CANCELLED
        assert projection.test_runs[0].status is ResultStatus.SKIPPED

    async def test_when_test_plan_identity_is_unsynchronized_expect_retry_wait(self) -> None:
        service, publications, _, _ = self._service(
            record=self._sync_record(), test_plan_synchronized=False
        )

        result = await service.process_next_publication()

        assert result is not None
        assert result.status is ViewerResultPublicationStatus.RETRY_WAIT
        assert "Test Plan identity is not synchronized" in (result.error or "")
        assert publications.saved == [result]

    @staticmethod
    def _service(
        record: ViewerSyncRecord | None,
        error_message: str | None = None,
        execution_status: ExecutionStatus = ExecutionStatus.FAILED,
        result_status: ResultStatus = ResultStatus.FAILED,
        test_plan_synchronized: bool = True,
        publisher: _Publisher | None = None,
        artifacts: tuple[TestResultArtifact, ...] = (),
        artifact_contents: tuple[str, ...] = (),
    ):
        test_case = a_test_case()
        execution = an_execution(
            test_case_ids=(test_case.identifier,),
            created_at=_CREATED_AT,
        ).start(_CREATED_AT)
        execution = (
            execution.cancel(_FINISHED_AT)
            if execution_status is ExecutionStatus.CANCELLED
            else execution.complete(execution_status, _FINISHED_AT)
        )
        test_result = TestResult(
            identifier=uuid4(),
            execution_id=execution.identifier,
            test_case_id=test_case.identifier,
            status=result_status,
            created_at=_CREATED_AT,
            started_at=_CREATED_AT,
            finished_at=_FINISHED_AT,
            duration_ms=1_000,
            error_code="HTTP_ASSERTION_FAILED",
            error_message=error_message,
        )
        artifacts = artifacts + tuple(
            TestResultArtifact(
                identifier=uuid4(),
                test_result_id=test_result.identifier,
                artifact_type=ArtifactType.LOG,
                storage_type=StorageType.DB,
                created_at=_FINISHED_AT,
                mime_type="text/plain; charset=utf-8",
                content=content,
            )
            for content in artifact_contents
        )
        publication = ViewerResultPublication(
            identifier=uuid4(),
            project_key=execution.project_key,
            execution_id=execution.identifier,
            viewer_type=ViewerType.XRAY,
            status=ViewerResultPublicationStatus.RUNNING,
            attempts=1,
            created_at=_FINISHED_AT,
            updated_at=_FINISHED_AT,
        )
        publications = _Publications(publication)
        publisher = publisher or _Publisher()
        test_plan = TestPlan(
            identifier=execution.test_plan_id,
            project_key=execution.project_key,
            plan_key="checkout-plan",
            version=1,
            name="Checkout plan",
            execution_mode=ExecutionMode.SEQUENTIAL,
            timeout_seconds=60,
            created_at=_CREATED_AT,
            created_by="author@example.test",
        )
        service = ViewerResultPublicationService(
            _Executions(execution),
            _Results(test_result, artifacts=artifacts),
            _Environments(
                Environment(
                    identifier=execution.environment_id,
                    environment_key="integration",
                    name="Integration",
                    created_at=_CREATED_AT,
                    created_by="author@example.test",
                    status=EnvironmentStatus.ACTIVE,
                )
            ),
            _TestCases(test_case),
            _TestPlans(test_plan),
            _ViewerRecords(
                {
                    ViewerEntityType.TEST_CASE: record,
                    ViewerEntityType.TEST_PLAN: (
                        TestViewerResultPublicationService._sync_plan_record(test_plan)
                        if test_plan_synchronized
                        else None
                    ),
                }
            ),
            publications,
            publisher,
            ViewerSettings(result_retry_backoff_seconds=1, result_retry_max_seconds=10),
        )
        return service, publications, publisher, test_result

    @staticmethod
    def _sync_record() -> ViewerSyncRecord:
        return ViewerSyncRecord(
            identifier=uuid4(),
            project_key="IAG",
            entity_type=ViewerEntityType.TEST_CASE,
            entity_key="checkout",
            entity_version=1,
            projected_version_id=uuid4(),
            viewer_type=ViewerType.XRAY,
            external_entity_key="IAG-1",
            external_entity_id="10001",
            sync_status=SyncStatus.SYNCED,
            created_at=_CREATED_AT,
        )

    @staticmethod
    def _sync_plan_record(test_plan: TestPlan) -> ViewerSyncRecord:
        return ViewerSyncRecord(
            identifier=uuid4(),
            project_key=test_plan.project_key,
            entity_type=ViewerEntityType.TEST_PLAN,
            entity_key=test_plan.logical_key,
            entity_version=test_plan.version,
            projected_version_id=uuid4(),
            viewer_type=ViewerType.XRAY,
            external_entity_key="IAG-2",
            external_entity_id="20001",
            sync_status=SyncStatus.SYNCED,
            created_at=_CREATED_AT,
        )
