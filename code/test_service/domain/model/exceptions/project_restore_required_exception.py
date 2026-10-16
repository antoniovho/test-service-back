"""Raised when registering a logically deleted project."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class ProjectRestoreRequiredException(DomainException):
    """Instruct callers to restore the existing logically deleted project."""

    def __init__(self, project_key: str) -> None:
        super().__init__(
            error_description=(
                f"project with key '{project_key}' is deleted; use "
                f"POST /v1/projects/{project_key}/restorations to restore it"
            ),
            error=DomainError.PROJECT_RESTORE_REQUIRED,
            origin=ErrorOrigin.USER,
        )
