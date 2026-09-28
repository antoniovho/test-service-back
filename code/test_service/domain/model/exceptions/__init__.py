"""Exceptions that communicate expected domain failures."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin
from test_service.domain.model.exceptions.invalid_action_exception import InvalidActionException
from test_service.domain.model.exceptions.invalid_artifact_storage_exception import (
    InvalidArtifactStorageException,
)
from test_service.domain.model.exceptions.invalid_definition_exception import (
    InvalidDefinitionException,
)
from test_service.domain.model.exceptions.invalid_environment_transition_exception import (
    InvalidEnvironmentTransitionException,
)
from test_service.domain.model.exceptions.invalid_execution_transition_exception import (
    InvalidExecutionTransitionException,
)
from test_service.domain.model.exceptions.invalid_lifecycle_transition_exception import (
    InvalidLifecycleTransitionException,
)
from test_service.domain.model.exceptions.invalid_precondition_exception import (
    InvalidPreconditionException,
)
from test_service.domain.model.exceptions.invalid_project_deletion_exception import (
    InvalidProjectDeletionException,
)
from test_service.domain.model.exceptions.invalid_secret_reference_exception import (
    InvalidSecretReferenceException,
)
from test_service.domain.model.exceptions.invalid_temporal_data_exception import (
    InvalidTemporalDataException,
)
from test_service.domain.model.exceptions.invalid_test_case_exception import (
    InvalidTestCaseException,
)
from test_service.domain.model.exceptions.invalid_test_plan_exception import (
    InvalidTestPlanException,
)
from test_service.domain.model.exceptions.invalid_test_set_exception import InvalidTestSetException
from test_service.domain.model.exceptions.precondition_project_mismatch_exception import (
    PreconditionProjectMismatchException,
)
from test_service.domain.model.exceptions.project_already_deleted_exception import (
    ProjectAlreadyDeletedException,
)
from test_service.domain.model.exceptions.project_already_exists_exception import (
    ProjectAlreadyExistsException,
)
from test_service.domain.model.exceptions.resolved_secret_not_allowed_exception import (
    ResolvedSecretNotAllowedException,
)

__all__ = [
    "DomainException",
    "EntityNotFoundException",
    "DomainError",
    "ErrorOrigin",
    "InvalidActionException",
    "InvalidArtifactStorageException",
    "InvalidDefinitionException",
    "InvalidEnvironmentTransitionException",
    "InvalidExecutionTransitionException",
    "InvalidLifecycleTransitionException",
    "InvalidPreconditionException",
    "InvalidProjectDeletionException",
    "InvalidSecretReferenceException",
    "InvalidTemporalDataException",
    "InvalidTestCaseException",
    "InvalidTestPlanException",
    "InvalidTestSetException",
    "PreconditionProjectMismatchException",
    "ProjectAlreadyDeletedException",
    "ProjectAlreadyExistsException",
    "ResolvedSecretNotAllowedException",
]
