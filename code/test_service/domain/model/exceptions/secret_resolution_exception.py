"""Raised when a secret reference cannot be turned into a usable value."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class SecretResolutionException(DomainException):
    """Raised when a secret reference cannot be turned into a usable value."""

    def __init__(
        self, error_description: str = DomainError.SECRET_RESOLUTION_FAILED.message
    ) -> None:
        """Initialize a secret-resolution failure.

        Args:
            error_description: Safe explanation of why the reference was not resolved. It
                must never contain the secret value or the rejected reference.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.SECRET_RESOLUTION_FAILED,
            origin=ErrorOrigin.PROVIDER,
        )
