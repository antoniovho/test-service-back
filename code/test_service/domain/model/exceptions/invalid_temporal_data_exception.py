"""Raised when an execution record has impossible timestamps or duration."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidTemporalDataException(DomainException):
    """Raised when an execution record has impossible timestamps or duration."""

    def __init__(
        self, error_description: str = DomainError.INVALID_TEMPORAL_DATA.message
    ) -> None:
        """Initialize an invalid temporal-data failure.

        Args:
            error_description: Safe explanation of the invalid temporal data.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_TEMPORAL_DATA,
            origin=ErrorOrigin.PROVIDER,
        )
