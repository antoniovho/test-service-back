"""Raised when a test set snapshot has an invalid version or item collection."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidTestSetException(DomainException):
    """Raised when a test set snapshot has an invalid version or item collection."""

    def __init__(self, error_description: str = DomainError.INVALID_TEST_SET.message) -> None:
        """Initialize an invalid-test-set failure.

        Args:
            error_description: Safe explanation of the invalid test set snapshot.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_TEST_SET,
            origin=ErrorOrigin.USER,
        )
