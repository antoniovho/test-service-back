"""Stable error codes and default descriptions for domain exceptions."""

from enum import Enum


class DomainError(Enum):
    """One entry per domain exception type: (code, default description)."""

    ENTITY_NOT_FOUND = ("ENTITY_NOT_FOUND", "Entity not found")
    PROJECT_ALREADY_EXISTS = ("PROJECT_ALREADY_EXISTS", "Project already exists")
    PROJECT_ALREADY_DELETED = ("PROJECT_ALREADY_DELETED", "Project is already deleted")
    INVALID_PROJECT_DELETION = ("INVALID_PROJECT_DELETION", "Invalid project deletion metadata")
    PRECONDITION_PROJECT_MISMATCH = (
        "PRECONDITION_PROJECT_MISMATCH",
        "Precondition snapshot does not belong to the requested project",
    )
    INVALID_ACTION = ("INVALID_ACTION", "Invalid action definition")
    INVALID_DEFINITION = ("INVALID_DEFINITION", "Invalid executable definition")
    INVALID_PRECONDITION = ("INVALID_PRECONDITION", "Invalid precondition snapshot")
    INVALID_TEST_CASE = ("INVALID_TEST_CASE", "Invalid test case snapshot")
    INVALID_TEST_PLAN = ("INVALID_TEST_PLAN", "Invalid test plan snapshot")
    INVALID_TEST_SET = ("INVALID_TEST_SET", "Invalid test set snapshot")
    INVALID_SECRET_REFERENCE = ("INVALID_SECRET_REFERENCE", "Invalid secret reference")
    RESOLVED_SECRET_NOT_ALLOWED = (
        "RESOLVED_SECRET_NOT_ALLOWED",
        "A resolved secret value is not allowed here",
    )
    INVALID_ENVIRONMENT_TRANSITION = (
        "INVALID_ENVIRONMENT_TRANSITION",
        "Invalid environment lifecycle transition",
    )
    INVALID_EXECUTION_TRANSITION = (
        "INVALID_EXECUTION_TRANSITION",
        "Invalid execution state transition",
    )
    INVALID_LIFECYCLE_TRANSITION = ("INVALID_LIFECYCLE_TRANSITION", "Invalid lifecycle transition")
    INVALID_TEMPORAL_DATA = ("INVALID_TEMPORAL_DATA", "Invalid temporal data")
    INVALID_ARTIFACT_STORAGE = ("INVALID_ARTIFACT_STORAGE", "Invalid artifact storage metadata")

    @property
    def code(self) -> str:
        """Stable machine-readable identifier for the failure."""
        return self.value[0]

    @property
    def message(self) -> str:
        """Default human-readable description for the failure."""
        return self.value[1]
