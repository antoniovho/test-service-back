"""Raised when artifact metadata conflicts with its storage backend."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidArtifactStorageException(DomainException):
    """Raised when artifact metadata conflicts with its storage backend."""

    def __init__(
        self, error_description: str = DomainError.INVALID_ARTIFACT_STORAGE.message
    ) -> None:
        """Initialize an invalid artifact-storage failure.

        Args:
            error_description: Safe explanation of the invalid artifact storage metadata.
        """
        super().__init__(
            error_description=error_description,
            error=DomainError.INVALID_ARTIFACT_STORAGE,
            origin=ErrorOrigin.PROVIDER,
        )
