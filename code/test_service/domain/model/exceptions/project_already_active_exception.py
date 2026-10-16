"""Raised when restoring a project that is already active."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class ProjectAlreadyActiveException(DomainException):
    """Raised when a project restoration targets an active project."""

    def __init__(self, error_description: str = DomainError.PROJECT_ALREADY_ACTIVE.message) -> None:
        super().__init__(
            error_description=error_description,
            error=DomainError.PROJECT_ALREADY_ACTIVE,
            origin=ErrorOrigin.USER,
        )
