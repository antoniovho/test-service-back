"""Raised when an action definition has an invalid identifier, type, or source."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidActionException(DomainException):
    """Raised when an action definition has an invalid identifier, type, or source."""

    def __init__(self, error_description: str = DomainError.INVALID_ACTION.message) -> None:
        """Initialize an invalid-action failure.

        Args:
            error_description: Safe explanation of the invalid action field.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_ACTION,
            origin=ErrorOrigin.USER,
        )
