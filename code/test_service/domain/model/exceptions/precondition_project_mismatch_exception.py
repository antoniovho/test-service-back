"""Raised when a precondition snapshot does not belong to the requested project."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class PreconditionProjectMismatchException(DomainException):
    """Raised when a precondition snapshot does not belong to the requested project."""

    def __init__(
        self, error_description: str = DomainError.PRECONDITION_PROJECT_MISMATCH.message
    ) -> None:
        """Initialize a precondition-project-mismatch failure.

        Args:
            error_description: Safe explanation of the ownership mismatch.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.PRECONDITION_PROJECT_MISMATCH,
            origin=ErrorOrigin.USER,
        )
