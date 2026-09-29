"""Base exceptions for domain rule violations."""

from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class DomainException(Exception):
    """Base class for expected failures caused by domain rules.

    Args:
        error: Stable machine-readable identifier for the failure.
        origin: Classification of what triggered the failure.
        error_description: Safe explanation of the failed domain rule.
        provider_name: Optional name of the external provider that caused the failure.
    """

    def __init__(
        self,
        error: DomainError,
        origin: ErrorOrigin,
        error_description: str | None = None,
        provider_name: str | None = None,
    ) -> None:

        self.error_description = error_description or error.message
        super().__init__(self.error_description)

        self.code = error.code
        self.origin = origin
        self.provider_name = provider_name
