"""Raised when a Test Case version already exists."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class TestCaseVersionAlreadyExistsException(DomainException):
    """Raised when a Test Case version already exists."""

    def __init__(
        self, error_description: str = DomainError.TEST_CASE_VERSION_ALREADY_EXISTS.message
    ) -> None:
        """Initialize a Test Case version conflict."""
        super().__init__(
            error_description=error_description,
            error=DomainError.TEST_CASE_VERSION_ALREADY_EXISTS,
            origin=ErrorOrigin.USER,
        )
