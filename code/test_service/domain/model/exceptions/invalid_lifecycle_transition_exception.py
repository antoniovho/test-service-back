"""Raised when a versioned snapshot's lifecycle transition is not allowed."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidLifecycleTransitionException(DomainException):
    """Raised when a versioned snapshot's lifecycle transition is not allowed."""

    def __init__(
        self, error_description: str = DomainError.INVALID_LIFECYCLE_TRANSITION.message
    ) -> None:
        """Initialize an invalid-lifecycle-transition failure.

        Args:
            error_description: Safe explanation of the disallowed transition.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_LIFECYCLE_TRANSITION,
            origin=ErrorOrigin.USER,
        )
