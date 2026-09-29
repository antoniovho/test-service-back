"""Raised when logically deleting a project that is already deleted."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class ProjectAlreadyDeletedException(DomainException):
    """Raised when logically deleting a project that is already deleted."""

    def __init__(
        self, error_description: str = DomainError.PROJECT_ALREADY_DELETED.message
    ) -> None:
        """Initialize a project-already-deleted failure.

        Args:
            error_description: Safe explanation of the conflicting state.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.PROJECT_ALREADY_DELETED,
            origin=ErrorOrigin.USER,
        )
