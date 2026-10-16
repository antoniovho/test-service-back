"""Raised when a deprecated Test Plan snapshot is used as a version source."""

from uuid import UUID

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class InvalidTestPlanVersionSourceException(DomainException):
    """Report that a deprecated Test Plan must be restored, not versioned."""

    def __init__(self, identifier: UUID) -> None:
        super().__init__(
            error=DomainError.INVALID_VERSION_SOURCE,
            origin=ErrorOrigin.USER,
            error_description=(
                f"deprecated test plan snapshot '{identifier}' cannot be used to create a new "
                "version; use its restoration endpoint instead"
            ),
        )
