"""Raised when persisted execution snapshots cannot be processed safely."""

from uuid import UUID

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class ExecutionManifestIntegrityException(DomainException):
    """Raised when an execution manifest is empty or references a missing snapshot."""

    def __init__(self, execution_id: UUID, snapshot_id: UUID | None = None) -> None:
        self.execution_id = execution_id
        self.snapshot_id = snapshot_id
        if snapshot_id is None:
            description = f"execution '{execution_id}' has no persisted effective composition"
        else:
            description = (
                f"execution '{execution_id}' references missing test case snapshot '{snapshot_id}'"
            )
        super().__init__(
            error=DomainError.EXECUTION_MANIFEST_INVALID,
            origin=ErrorOrigin.INTERNAL,
            error_description=description,
        )
