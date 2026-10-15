"""External project provider exceptions."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class ExternalProjectProviderException(DomainException):
    """Validation cannot safely establish the state of an external project."""

    def __init__(
        self,
        error_description: str | None = None,
        provider_name: str | None = None,
    ) -> None:
        super().__init__(
            DomainError.ENTITY_NOT_FOUND,
            ErrorOrigin.PROVIDER,
            error_description,
            provider_name=provider_name,
        )
