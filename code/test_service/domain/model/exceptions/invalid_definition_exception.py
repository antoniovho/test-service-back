"""Raised when an executable definition violates its schema or structural invariants."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidDefinitionException(DomainException):
    """Raised when an executable definition violates its schema or structural invariants."""

    def __init__(self, error_description: str = DomainError.INVALID_DEFINITION.message) -> None:
        """Initialize an invalid-definition failure.

        Args:
            error_description: Safe explanation of the invalid definition.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_DEFINITION,
            origin=ErrorOrigin.USER,
        )
