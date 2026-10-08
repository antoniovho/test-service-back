"""Mapping between Execution domain objects and SQLAlchemy DTOs."""

from collections.abc import Mapping

from test_service.domain.model.execution.environment import SecretReference
from test_service.domain.model.execution.execution import Execution, ExecutionStatus, TriggerType
from test_service.infrastructure.adapters.output.execution.executions.persistence.dtos.execution_dto import (  # noqa: E501
    ExecutionDTO,
)


class ExecutionPersistenceMapper:
    """Translate Execution data at the domain and persistence boundary."""

    @staticmethod
    def to_dto(execution: Execution) -> ExecutionDTO:
        """Create a persistence DTO from an Execution aggregate."""
        return ExecutionDTO(
            id=execution.identifier,
            project_key=execution.project_key,
            test_plan_id=execution.test_plan_id,
            environment_id=execution.environment_id,
            test_case_ids=list(execution.test_case_ids),
            environment_snapshot=ExecutionPersistenceMapper._to_storage_snapshot(
                execution.environment_snapshot
            ),
            trigger_type=execution.trigger_type.value,
            triggered_by=execution.triggered_by,
            status=execution.status.value,
            runner_identifier=execution.runner_identifier,
            runner_version=execution.runner_version,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            duration_ms=execution.duration_ms,
            created_at=execution.created_at,
        )

    @staticmethod
    def to_domain(execution: ExecutionDTO) -> Execution:
        """Create an Execution aggregate from a persistence DTO."""
        return Execution(
            identifier=execution.id,
            project_key=execution.project_key,
            test_plan_id=execution.test_plan_id,
            environment_id=execution.environment_id,
            test_case_ids=tuple(execution.test_case_ids),
            environment_snapshot=ExecutionPersistenceMapper._to_domain_snapshot(
                execution.environment_snapshot
            ),
            trigger_type=TriggerType(execution.trigger_type),
            triggered_by=execution.triggered_by,
            status=ExecutionStatus(execution.status),
            runner_identifier=execution.runner_identifier,
            runner_version=execution.runner_version,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            duration_ms=execution.duration_ms,
            created_at=execution.created_at,
        )

    @staticmethod
    def _to_storage_snapshot(snapshot: Mapping[str, object] | None) -> dict[str, object]:
        return {
            key: (
                {"provider": value.provider, "referenceKey": value.reference_key}
                if isinstance(value, SecretReference)
                else value
            )
            for key, value in (snapshot or {}).items()
        }

    @staticmethod
    def _to_domain_snapshot(snapshot: dict[str, object]) -> dict[str, object] | None:
        if not snapshot:
            return None
        return {
            key: (
                SecretReference(value["provider"], value["referenceKey"])
                if isinstance(value, dict) and set(value) == {"provider", "referenceKey"}
                else value
            )
            for key, value in snapshot.items()
        }
