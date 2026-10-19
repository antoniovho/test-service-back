"""Raised when activating an execution environment that is already active."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class EnvironmentAlreadyActiveException(DomainException):
    """Raised when an activation request targets an active environment."""

    def __init__(self, environment_key: str) -> None:
        super().__init__(
            error_description=f"Environment '{environment_key}' is already active.",
            error=DomainError.ENVIRONMENT_ALREADY_ACTIVE,
            origin=ErrorOrigin.USER,
        )
