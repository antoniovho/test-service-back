"""Raised when registering a project whose key is already in the catalog."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class ProjectAlreadyExistsException(DomainException):
    """Raised when registering a project whose key is already in the catalog."""

    def __init__(
        self, error_description: str = DomainError.PROJECT_ALREADY_EXISTS.message
    ) -> None:
        """Initialize a project-already-exists failure.

        Args:
            error_description: Safe explanation of the conflicting state.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.PROJECT_ALREADY_EXISTS,
            origin=ErrorOrigin.USER,
        )
