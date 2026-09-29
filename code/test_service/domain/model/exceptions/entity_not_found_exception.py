"""Raised when a requested domain entity does not exist."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class EntityNotFoundException(DomainException):
    """Raised when a requested domain entity does not exist."""

    def __init__(self, entity_name: str, entity_identifier: str) -> None:
        """Initialize a missing-entity failure.

        Args:
            entity_name: Name of the missing domain entity.
            entity_identifier: Identifier supplied for the entity lookup.
        """
        super().__init__(
            error_description=f"{entity_name} with identifier '{entity_identifier}' was not found",
            error=DomainError.ENTITY_NOT_FOUND,
            origin=ErrorOrigin.USER,
        )
