"""Map immutable execution evidence between persistence and domain representations."""
# ruff: noqa: E501

from test_service.domain.model.execution.execution import (
    ActionResult,
    ArtifactType,
    ResultStatus,
    StorageType,
    TestResult,
    TestResultArtifact,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.dtos.execution_result_dtos import (  # noqa: E501
    ActionResultDTO,
    TestResultArtifactDTO,
    TestResultDTO,
)


class ExecutionResultsPersistenceMapper:
    """Translate immutable execution evidence DTOs to domain values."""

    @staticmethod
    def to_test_result_dto(value: TestResult) -> TestResultDTO:
        return TestResultDTO(
            id=value.identifier,
            execution_id=value.execution_id,
            test_case_id=value.test_case_id,
            status=value.status.value,
            created_at=value.created_at,
            started_at=value.started_at,
            finished_at=value.finished_at,
            duration_ms=value.duration_ms,
            error_code=value.error_code,
            error_message=value.error_message,
        )

    @staticmethod
    def to_action_result_dto(value: ActionResult) -> ActionResultDTO:
        return ActionResultDTO(
            id=value.identifier,
            test_result_id=value.test_result_id,
            action_id=value.action_id,
            action_type=value.action_type,
            status=value.status.value,
            created_at=value.created_at,
            expected=dict(value.expected) if value.expected else None,
            actual=dict(value.actual) if value.actual else None,
            output=dict(value.output) if value.output else None,
            started_at=value.started_at,
            finished_at=value.finished_at,
            duration_ms=value.duration_ms,
            error_code=value.error_code,
            error_message=value.error_message,
        )

    @staticmethod
    def to_artifact_dto(value: TestResultArtifact) -> TestResultArtifactDTO:
        return TestResultArtifactDTO(
            id=value.identifier,
            test_result_id=value.test_result_id,
            action_result_id=value.action_result_id,
            artifact_type=value.artifact_type.value,
            storage_type=value.storage_type.value,
            storage_uri=value.storage_uri,
            content_hash=value.content_hash,
            size_bytes=value.size_bytes,
            mime_type=value.mime_type,
            created_at=value.created_at,
        )

    @staticmethod
    def to_test_result(dto: TestResultDTO) -> TestResult:
        return TestResult(
            identifier=dto.id,
            execution_id=dto.execution_id,
            test_case_id=dto.test_case_id,
            status=ResultStatus(dto.status),
            created_at=dto.created_at,
            started_at=dto.started_at,
            finished_at=dto.finished_at,
            duration_ms=dto.duration_ms,
            error_code=dto.error_code,
            error_message=dto.error_message,
        )

    @staticmethod
    def to_action_result(dto: ActionResultDTO) -> ActionResult:
        return ActionResult(
            identifier=dto.id,
            test_result_id=dto.test_result_id,
            action_id=dto.action_id,
            action_type=dto.action_type,
            status=ResultStatus(dto.status),
            created_at=dto.created_at,
            expected=dto.expected,
            actual=dto.actual,
            output=dto.output,
            started_at=dto.started_at,
            finished_at=dto.finished_at,
            duration_ms=dto.duration_ms,
            error_code=dto.error_code,
            error_message=dto.error_message,
        )

    @staticmethod
    def to_artifact(dto: TestResultArtifactDTO) -> TestResultArtifact:
        return TestResultArtifact(
            identifier=dto.id,
            test_result_id=dto.test_result_id,
            action_result_id=dto.action_result_id,
            artifact_type=ArtifactType(dto.artifact_type),
            storage_type=StorageType(dto.storage_type),
            storage_uri=dto.storage_uri,
            content_hash=dto.content_hash,
            size_bytes=dto.size_bytes,
            mime_type=dto.mime_type,
            created_at=dto.created_at,
        )
