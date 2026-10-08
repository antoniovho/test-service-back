"""Raised when an execution's accepted runner cannot process it."""

from uuid import UUID

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class ExecutionRunnerUnavailableException(DomainException):
    """Raised when the available runner differs from the runner accepted at scheduling."""

    def __init__(
        self,
        execution_id: UUID,
        accepted_identifier: str | None,
        accepted_version: str | None,
        available_identifier: str,
        available_version: str,
    ) -> None:
        self.execution_id = execution_id
        self.accepted_identifier = accepted_identifier
        self.accepted_version = accepted_version
        self.available_identifier = available_identifier
        self.available_version = available_version
        super().__init__(
            error=DomainError.EXECUTION_RUNNER_UNAVAILABLE,
            origin=ErrorOrigin.INTERNAL,
            error_description=(
                f"execution '{execution_id}' requires runner "
                f"'{accepted_identifier}' version '{accepted_version}', but available runner "
                f"is '{available_identifier}' version '{available_version}'"
            ),
        )
