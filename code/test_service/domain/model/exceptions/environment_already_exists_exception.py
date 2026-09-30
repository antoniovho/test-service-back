"""Raised when creating an existing execution environment key."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class EnvironmentAlreadyExistsException(DomainException):
    """Raised when an execution environment key is already registered."""

    def __init__(self, environment_key: str) -> None:
        super().__init__(
            error_description=f"Environment with key '{environment_key}' already exists.",
            error=DomainError.ENVIRONMENT_ALREADY_EXISTS,
            origin=ErrorOrigin.USER,
        )
