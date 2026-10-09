"""Raised when a project key does not follow the accepted key format."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidProjectKeyException(DomainException):
    """Raised when a project key does not follow the accepted key format."""

    def __init__(self, error_description: str = DomainError.INVALID_PROJECT_KEY.message) -> None:
        """Initialize an invalid-project-key failure.

        Args:
            error_description: Safe explanation of the accepted key format.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_PROJECT_KEY,
            origin=ErrorOrigin.USER,
        )
