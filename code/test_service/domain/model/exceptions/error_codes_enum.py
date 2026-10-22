"""Stable error codes and default descriptions for domain exceptions."""

from enum import Enum


class DomainError(Enum):
    """One entry per domain exception type: (code, default description)."""

    ENTITY_NOT_FOUND = ("ENTITY_NOT_FOUND", "Entity not found")
    ENTITY_FORBIDDEN = ("ENTITY_FORBIDDEN", "Access to the entity is forbidden")
    PROJECT_ALREADY_EXISTS = ("PROJECT_ALREADY_EXISTS", "Project already exists")
    PROJECT_ALREADY_DELETED = ("PROJECT_ALREADY_DELETED", "Project is already deleted")
    PROJECT_ALREADY_ACTIVE = ("PROJECT_ALREADY_ACTIVE", "Project is already active")
    PROJECT_RESTORE_REQUIRED = (
        "PROJECT_RESTORE_REQUIRED",
        "Project is deleted; use the restore project endpoint",
    )
    TEST_CASE_VERSION_ALREADY_EXISTS = (
        "TEST_CASE_VERSION_ALREADY_EXISTS",
        "Test case version already exists",
    )
    TEST_CASE_ALREADY_EXISTS = ("TEST_CASE_ALREADY_EXISTS", "Test case already exists")
    TEST_SET_ALREADY_EXISTS = ("TEST_SET_ALREADY_EXISTS", "Test set already exists")
    TEST_PLAN_ALREADY_EXISTS = ("TEST_PLAN_ALREADY_EXISTS", "Test plan already exists")
    PRECONDITION_ALREADY_EXISTS = ("PRECONDITION_ALREADY_EXISTS", "Precondition already exists")
    ENVIRONMENT_ALREADY_EXISTS = ("ENVIRONMENT_ALREADY_EXISTS", "Environment already exists")
    ENVIRONMENT_ALREADY_ACTIVE = ("ENVIRONMENT_ALREADY_ACTIVE", "Environment is already active")
    ENVIRONMENT_ALREADY_INACTIVE = (
        "ENVIRONMENT_ALREADY_INACTIVE",
        "Environment is already inactive",
    )
    INVALID_PROJECT_DELETION = ("INVALID_PROJECT_DELETION", "Invalid project deletion metadata")
    INVALID_PROJECT_KEY = ("INVALID_PROJECT_KEY", "Invalid project key")
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
    SECRET_RESOLUTION_FAILED = (
        "SECRET_RESOLUTION_FAILED",
        "Secret reference could not be resolved",
    )
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
    EXECUTION_RUNNER_UNAVAILABLE = (
        "EXECUTION_RUNNER_UNAVAILABLE",
        "Accepted execution runner is unavailable",
    )
    EXECUTION_MANIFEST_INVALID = (
        "EXECUTION_MANIFEST_INVALID",
        "Execution manifest is invalid",
    )
    INVALID_LIFECYCLE_TRANSITION = ("INVALID_LIFECYCLE_TRANSITION", "Invalid lifecycle transition")
    INVALID_VERSION_SOURCE = ("INVALID_VERSION_SOURCE", "Invalid version source")
    INVALID_TEMPORAL_DATA = ("INVALID_TEMPORAL_DATA", "Invalid temporal data")
    INVALID_ARTIFACT_STORAGE = ("INVALID_ARTIFACT_STORAGE", "Invalid artifact storage metadata")
    VIEWER_PROJECTION_INVALID = (
        "VIEWER_PROJECTION_INVALID",
        "Viewer projection cannot be built",
    )
    VIEWER_RESULT_PUBLICATION_RETRYABLE = (
        "VIEWER_RESULT_PUBLICATION_RETRYABLE",
        "Viewer result publication can be retried",
    )
    VIEWER_RESULT_PUBLICATION_PERMANENT = (
        "VIEWER_RESULT_PUBLICATION_PERMANENT",
        "Viewer result publication cannot be completed",
    )

    @property
    def code(self) -> str:
        """Stable machine-readable identifier for the failure."""
        return self.value[0]

    @property
    def message(self) -> str:
        """Default human-readable description for the failure."""
        return self.value[1]
