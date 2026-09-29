"""Raised when a project's deletion metadata is inconsistent with its lifecycle state."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidProjectDeletionException(DomainException):
    """Raised when a project's deletion metadata is inconsistent with its lifecycle state."""

    def __init__(
        self, error_description: str = DomainError.INVALID_PROJECT_DELETION.message
    ) -> None:
        """Initialize an invalid-project-deletion failure.

        Args:
            error_description: Safe explanation of the invalid deletion metadata.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_PROJECT_DELETION,
            origin=ErrorOrigin.INTERNAL,
        )
