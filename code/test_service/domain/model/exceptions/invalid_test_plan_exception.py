"""Raised when a test plan snapshot has invalid references, timeout, or execution mode."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidTestPlanException(DomainException):
    """Raised when a test plan snapshot has invalid references, timeout, or execution mode."""

    def __init__(self, error_description: str = DomainError.INVALID_TEST_PLAN.message) -> None:
        """Initialize an invalid-test-plan failure.

        Args:
            error_description: Safe explanation of the invalid test plan snapshot.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_TEST_PLAN,
            origin=ErrorOrigin.USER,
        )
