"""Raised when a secret reference is missing its provider or lookup key."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidSecretReferenceException(DomainException):
    """Raised when a secret reference is missing its provider or lookup key."""

    def __init__(
        self, error_description: str = DomainError.INVALID_SECRET_REFERENCE.message
    ) -> None:
        """Initialize an invalid-secret-reference failure.

        Args:
            error_description: Safe explanation of the invalid secret reference.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_SECRET_REFERENCE,
            origin=ErrorOrigin.USER,
        )
