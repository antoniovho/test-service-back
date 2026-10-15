"""Failure raised when a Viewer projection cannot be built safely."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class ViewerProjectionIntegrityException(DomainException):
    """Raised when a Viewer projection references unavailable local or remote dependencies."""

    def __init__(self, error_description: str) -> None:
        super().__init__(
            error=DomainError.VIEWER_PROJECTION_INVALID,
            origin=ErrorOrigin.INTERNAL,
            error_description=error_description,
        )
