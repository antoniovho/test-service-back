"""Raised when a test case snapshot has an invalid version, timeout, or references."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidTestCaseException(DomainException):
    """Raised when a test case snapshot has an invalid version, timeout, or references."""

    def __init__(self, error_description: str = DomainError.INVALID_TEST_CASE.message) -> None:
        """Initialize an invalid-test-case failure.

        Args:
            error_description: Safe explanation of the invalid test case snapshot.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_TEST_CASE,
            origin=ErrorOrigin.USER,
        )
