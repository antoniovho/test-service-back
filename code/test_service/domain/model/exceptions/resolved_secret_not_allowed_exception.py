"""Raised when a secret-like configuration key holds a raw value instead of a reference."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class ResolvedSecretNotAllowedException(DomainException):
    """Raised when a secret-like configuration key holds a raw value instead of a reference."""

    def __init__(
        self, error_description: str = DomainError.RESOLVED_SECRET_NOT_ALLOWED.message
    ) -> None:
        """Initialize a resolved-secret-not-allowed failure.

        Args:
            error_description: Safe explanation of the disallowed raw secret value.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.RESOLVED_SECRET_NOT_ALLOWED,
            origin=ErrorOrigin.USER,
        )
