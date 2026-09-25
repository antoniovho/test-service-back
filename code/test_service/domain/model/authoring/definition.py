"""Executable test-definition value objects."""

from collections.abc import Mapping
from dataclasses import dataclass

from test_service.domain.commons.immutable import freeze_mapping
from test_service.domain.model.exceptions.domain_exception import ValidationException

DEFINITION_SCHEMA_VERSION = "1.0"
SUPPORTED_DEFINITION_SCHEMA_VERSIONS = "1.0"


@dataclass(frozen=True, slots=True)
class Action:
    """One ordered executable action in a definition.

    Args:
        identifier: Identifier unique within the containing definition.
        action_type: Action Registry type that validates the configuration.
        configuration: Dynamic action-specific configuration.
        source: Optional action provider or source.

    Raises:
        ValidationException: If an identifier, action type, or source is invalid.
    """

    identifier: str
    action_type: str
    configuration: Mapping[str, object]
    source: str | None = None

    def __post_init__(self) -> None:
        """Validate Action fields and freeze the mutable configuration mapping.

        Raises:
            ValidationException: If a required text field is empty.
        """
        self._validate_text(self.identifier, "action identifier")
        self._validate_text(self.action_type, "action type")
        if self.source is not None:
            self._validate_text(self.source, "action source")
        object.__setattr__(self, "configuration", freeze_mapping(self.configuration))

    @staticmethod
    def _validate_text(value: str, label: str) -> None:
        if not value or not isinstance(value, str):
            raise ValidationException(
                f"{label} must not be empty or non-string",
                "INVALID_ACTION",
            )


@dataclass(frozen=True, slots=True)
class Definition:
    """Ordered, executable definition interpreted by the test runner.

    Args:
        variables: String variables available to the actions.
        actions: Ordered actions to execute.
        schema_version: Version of the compiler schema.

    Raises:
        ValidationException: If the schema, variables, actions, or action identifiers are invalid.
    """

    variables: Mapping[str, str]
    actions: tuple[Action, ...]
    schema_version: str = DEFINITION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate Definition invariants and freeze the mutable variables mapping.

        Raises:
            ValidationException: If the schema is unsupported or action identifiers are duplicated.
        """
        if self.schema_version not in SUPPORTED_DEFINITION_SCHEMA_VERSIONS:
            raise ValidationException(
                f"definition schema version must be one of {SUPPORTED_DEFINITION_SCHEMA_VERSIONS}, "
                "other versions are not supported",
                "INVALID_DEFINITION",
            )
        if not self.actions:
            raise ValidationException(
                "definition must include at least one action",
                "INVALID_DEFINITION",
            )
        if len({action.identifier for action in self.actions}) != len(self.actions):
            raise ValidationException(
                "definition action identifiers must be unique",
                "INVALID_DEFINITION",
            )
        if any(not name for name in self.variables):
            raise ValidationException(
                "definition variable names must not be empty",
                "INVALID_DEFINITION",
            )
        object.__setattr__(self, "variables", freeze_mapping(self.variables))
