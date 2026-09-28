"""Raised when a precondition snapshot has an invalid version."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidPreconditionException(DomainException):
    """Raised when a precondition snapshot has an invalid version."""

    def __init__(self, error_description: str = DomainError.INVALID_PRECONDITION.message) -> None:
        """Initialize an invalid-precondition failure.

        Args:
            error_description: Safe explanation of the invalid precondition snapshot.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_PRECONDITION,
            origin=ErrorOrigin.USER,
        )
