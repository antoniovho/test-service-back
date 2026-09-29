"""Raised when a requested domain entity does not exist."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class EntityNotFoundException(DomainException):
    """Raised when a requested domain entity does not exist."""

    def __init__(self, entity_name: str, entity_identifier: str, scope: str | None = None) -> None:
        """Initialize a missing-entity failure.

        Args:
            entity_name: Name of the missing domain entity.
            entity_identifier: Identifier supplied for the entity lookup.
            scope: Optional scope in which the entity was requested.
        """
        scope_suffix = f" in {scope}." if scope is not None else ""
        super().__init__(
            error_description=f"{entity_name} '{entity_identifier}' was not found{scope_suffix}",
            error=DomainError.ENTITY_NOT_FOUND,
            origin=ErrorOrigin.USER,
        )
