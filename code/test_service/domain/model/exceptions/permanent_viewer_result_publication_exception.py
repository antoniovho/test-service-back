"""Failure that prevents a Viewer result publication from succeeding."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class PermanentViewerResultPublicationError(DomainException):
    """Raised when publishing results cannot succeed without intervention."""

    def __init__(
        self,
        error_description: str,
        origin: ErrorOrigin = ErrorOrigin.INTERNAL,
        provider_name: str | None = None,
    ) -> None:
        super().__init__(
            DomainError.VIEWER_RESULT_PUBLICATION_PERMANENT,
            origin,
            error_description,
            provider_name,
        )
