"""Base exceptions for domain rule violations."""


class DomainException(Exception):
    """Base class for expected failures caused by domain rules.

    Args:
        message: Safe explanation of the failed domain rule.
        code: Stable machine-readable identifier for the failure.
    """

    def __init__(self, message: str, code: str) -> None:
        """Initialize a domain exception.

        Args:
            message: Safe explanation of the failed domain rule.
            code: Stable machine-readable identifier for the failure.
        """
        super().__init__(message)
        self.code = code


class EntityNotFoundException(DomainException):
    """Raised when a requested domain entity does not exist.

    Args:
        entity_name: Name of the missing domain entity.
        entity_identifier: Identifier supplied for the entity lookup.
    """

    def __init__(self, entity_name: str, entity_identifier: str) -> None:
        """Initialize a missing-entity failure.

        Args:
            entity_name: Name of the missing domain entity.
            entity_identifier: Identifier supplied for the entity lookup.
        """
        super().__init__(
            message=f"{entity_name} with identifier '{entity_identifier}' was not found",
            code="ENTITY_NOT_FOUND",
        )


class BusinessRuleViolationException(DomainException):
    """Raised when an operation violates a domain invariant.

    Args:
        message: Safe explanation of the violated domain rule.
        code: Stable machine-readable identifier for the failure.
    """


class ConflictException(DomainException):
    """Raised when an operation conflicts with the current domain state.

    Args:
        message: Safe explanation of the conflicting state.
        code: Stable machine-readable identifier for the failure.
    """


class ValidationException(DomainException):
    """Raised when a domain command has invalid semantic values.

    Args:
        message: Safe explanation of the invalid value.
        code: Stable machine-readable identifier for the failure.
    """


class InvalidTemporalDataException(BusinessRuleViolationException):
    """Raised when an execution record has impossible timestamps or duration.

    Args:
        message: Safe explanation of the invalid temporal data.
    """

    def __init__(self, message: str) -> None:
        """Initialize an invalid temporal-data failure.

        Args:
            message: Safe explanation of the invalid temporal data.
        """
        super().__init__(message, "INVALID_TEMPORAL_DATA")


class InvalidArtifactStorageException(BusinessRuleViolationException):
    """Raised when artifact metadata conflicts with its storage backend.

    Args:
        message: Safe explanation of the invalid artifact storage metadata.
    """

    def __init__(self, message: str) -> None:
        """Initialize an invalid artifact-storage failure.

        Args:
            message: Safe explanation of the invalid artifact storage metadata.
        """
        super().__init__(message, "INVALID_ARTIFACT_STORAGE")
