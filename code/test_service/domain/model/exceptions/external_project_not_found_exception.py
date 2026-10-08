"""External Project validation exceptions."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class ExternalProjectNotFoundException(DomainException):
    """The supplied key does not name a usable external project."""

    def __init__(self, project_key: str) -> None:
        super().__init__(
            DomainError.ENTITY_NOT_FOUND,
            ErrorOrigin.USER,
            f"project '{project_key}' does not exist in the external project catalog",
        )


class ExternalProjectProviderException(DomainException):
    """Validation cannot safely establish the state of an external project."""

    def __init__(self) -> None:
        super().__init__(DomainError.ENTITY_NOT_FOUND, ErrorOrigin.PROVIDER, provider_name="Jira")
