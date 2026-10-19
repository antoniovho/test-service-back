"""Raised when deactivating an execution environment that is already inactive."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class EnvironmentAlreadyInactiveException(DomainException):
    """Raised when a deactivation request targets an inactive environment."""

    def __init__(self, environment_key: str) -> None:
        super().__init__(
            error_description=f"Environment '{environment_key}' is already inactive.",
            error=DomainError.ENVIRONMENT_ALREADY_INACTIVE,
            origin=ErrorOrigin.USER,
        )
