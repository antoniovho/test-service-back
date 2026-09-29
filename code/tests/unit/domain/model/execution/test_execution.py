from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from test_service.domain.model.exceptions.invalid_artifact_storage_exception import (
    InvalidArtifactStorageException,
)
from test_service.domain.model.exceptions.invalid_execution_transition_exception import (
    InvalidExecutionTransitionException,
)
from test_service.domain.model.exceptions.invalid_temporal_data_exception import (
    InvalidTemporalDataException,
)
from test_service.domain.model.execution.execution import (
    ActionResult,
    ArtifactType,
    Execution,
    ExecutionStatus,
    ResultStatus,
    StorageType,
    TestResultArtifact,
    TriggerType,
)

CREATED_AT = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)


def _execution(**overrides: object) -> Execution:
    fields = {
        "identifier": uuid4(),
        "project_key": "IAG",
        "test_plan_id": uuid4(),
        "environment_id": uuid4(),
        "trigger_type": TriggerType.API,
        "created_at": CREATED_AT,
    }
    fields.update(overrides)
    return Execution(**fields)


class TestExecutionStart:
    def test_when_created_expect_running_with_started_at(self):
        execution = _execution()
        started_at = CREATED_AT + timedelta(seconds=5)

        started = execution.start(started_at)

        assert started.status is ExecutionStatus.RUNNING
        assert started.started_at == started_at

    @pytest.mark.parametrize(
        "status", [ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED], ids=["running", "cancelled"]
    )
    def test_when_not_created_expect_exception(self, status):
        execution = _execution(status=status)

        with pytest.raises(InvalidExecutionTransitionException) as exc:
            execution.start(CREATED_AT)

        assert exc.value.code == "INVALID_EXECUTION_TRANSITION"


class TestExecutionComplete:
    def test_when_running_expect_terminal_with_duration(self):
        started_at = CREATED_AT + timedelta(seconds=5)
        finished_at = started_at + timedelta(seconds=120)
        execution = _execution(status=ExecutionStatus.RUNNING, started_at=started_at)

        completed = execution.complete(ExecutionStatus.PASSED, finished_at)

        assert completed.status is ExecutionStatus.PASSED
        assert completed.finished_at == finished_at
        assert completed.duration_ms == 120000

    def test_when_not_running_expect_exception(self):
        execution = _execution(status=ExecutionStatus.CREATED)

        with pytest.raises(InvalidExecutionTransitionException) as exc:
            execution.complete(ExecutionStatus.PASSED, CREATED_AT)

        assert exc.value.code == "INVALID_EXECUTION_TRANSITION"

    def test_when_target_status_not_runner_outcome_expect_exception(self):
        execution = _execution(status=ExecutionStatus.RUNNING, started_at=CREATED_AT)

        with pytest.raises(InvalidExecutionTransitionException) as exc:
            execution.complete(ExecutionStatus.CANCELLED, CREATED_AT)

        assert exc.value.code == "INVALID_EXECUTION_TRANSITION"


class TestExecutionCancel:
    @pytest.mark.parametrize(
        "status", [ExecutionStatus.CREATED, ExecutionStatus.RUNNING], ids=["created", "running"]
    )
    def test_when_not_terminal_expect_cancelled(self, status):
        execution = _execution(status=status)

        cancelled = execution.cancel()

        assert cancelled.status is ExecutionStatus.CANCELLED

    def test_when_running_with_started_at_expect_duration_computed(self):
        started_at = CREATED_AT + timedelta(seconds=5)
        finished_at = started_at + timedelta(seconds=30)
        execution = _execution(status=ExecutionStatus.RUNNING, started_at=started_at)

        cancelled = execution.cancel(finished_at)

        assert cancelled.duration_ms == 30000

    def test_when_already_terminal_expect_exception(self):
        execution = _execution(status=ExecutionStatus.PASSED)

        with pytest.raises(InvalidExecutionTransitionException) as exc:
            execution.cancel()

        assert exc.value.code == "INVALID_EXECUTION_TRANSITION"


class TestExecutionTemporalValidation:
    def test_when_finish_precedes_start_expect_exception(self):
        finished_at = CREATED_AT - timedelta(seconds=1)

        with pytest.raises(InvalidTemporalDataException):
            _execution(
                started_at=CREATED_AT,
                finished_at=finished_at,
            )

    def test_when_duration_negative_expect_exception(self):
        with pytest.raises(InvalidTemporalDataException):
            _execution(duration_ms=-1)


class TestActionResultImmutability:
    def test_when_expected_mutated_after_creation_expect_action_result_unaffected(self):
        expected = {"statusCode": 200}
        action_result = ActionResult(
            identifier=uuid4(),
            test_result_id=uuid4(),
            action_id="login",
            action_type="HTTP_REQUEST",
            status=ResultStatus.PASSED,
            expected=expected,
        )

        expected["statusCode"] = 500

        assert action_result.expected["statusCode"] == 200


class TestTestResultArtifact:
    def test_when_db_storage_with_uri_expect_exception(self):
        with pytest.raises(InvalidArtifactStorageException):
            TestResultArtifact(
                identifier=uuid4(),
                test_result_id=uuid4(),
                artifact_type=ArtifactType.LOG,
                storage_type=StorageType.DB,
                created_at=CREATED_AT,
                storage_uri="https://storage.example.com/artifacts/abc",
            )

    def test_when_object_storage_without_uri_expect_exception(self):
        with pytest.raises(InvalidArtifactStorageException):
            TestResultArtifact(
                identifier=uuid4(),
                test_result_id=uuid4(),
                artifact_type=ArtifactType.RESPONSE,
                storage_type=StorageType.OBJECT_STORAGE,
                created_at=CREATED_AT,
            )

    def test_when_negative_size_expect_exception(self):
        with pytest.raises(InvalidArtifactStorageException):
            TestResultArtifact(
                identifier=uuid4(),
                test_result_id=uuid4(),
                artifact_type=ArtifactType.LOG,
                storage_type=StorageType.DB,
                created_at=CREATED_AT,
                size_bytes=-1,
            )
