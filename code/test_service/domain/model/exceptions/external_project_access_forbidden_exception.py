"""External project access-denied exceptions."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class ExternalProjectForbiddenException(DomainException):
    """The external project provider denied access to the requested project."""

    def __init__(self, provider_name: str | None = None) -> None:
        super().__init__(
            DomainError.ENTITY_FORBIDDEN,
            ErrorOrigin.PROVIDER,
            provider_name=provider_name,
        )
