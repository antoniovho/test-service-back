"""Raised when creating an existing logical Precondition key."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class PreconditionAlreadyExistsException(DomainException):
    """Raised when a Precondition key already has an immutable version."""

    def __init__(self, project_key: str, precondition_key: str) -> None:
        super().__init__(
            error_description=(
                f"Precondition with key '{precondition_key}' already exists in project "
                f"'{project_key}'. Use POST /v1/projects/{project_key}/preconditions/"
                "{preconditionId}/versions to create a new version."
            ),
            error=DomainError.PRECONDITION_ALREADY_EXISTS,
            origin=ErrorOrigin.USER,
        )
