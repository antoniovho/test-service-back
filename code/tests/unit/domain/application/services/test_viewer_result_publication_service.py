from datetime import UTC, datetime
from uuid import uuid4

from test_service.config import ViewerSettings
from test_service.domain.application.queries.pagination import Page
from test_service.domain.application.services.viewer_result_publication_service import (
    ViewerResultPublicationService,
)
from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.execution.environment import Environment, EnvironmentStatus
from test_service.domain.model.execution.execution import ExecutionStatus, ResultStatus, TestResult
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
    def __init__(self, result: TestResult) -> None:
        self._result = result

    async def find_results_page(self, _, __):
        return Page((self._result,), 1)


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

    async def test_when_test_identity_is_unsynchronized_expect_retry_wait(self) -> None:
        service, publications, _, test_result = self._service(record=None)

        result = await service.process_next_publication()

        assert result is not None
        assert result.status is ViewerResultPublicationStatus.RETRY_WAIT
        assert "not synchronized" in (result.error or "")
        assert str(publications._publication.identifier) in (result.error or "")
        assert str(publications._publication.execution_id) in (result.error or "")
        assert str(test_result.identifier) in (result.error or "")
        assert str(test_result.test_case_id) in (result.error or "")
        assert publications.saved == [result]

    async def test_when_result_is_resolved_expect_safe_projection_and_persisted_identity(
        self,
    ) -> None:
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
        publisher = _Publisher()
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
            _Results(test_result),
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
