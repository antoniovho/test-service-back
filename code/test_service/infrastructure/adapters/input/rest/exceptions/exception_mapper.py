"""Map domain exceptions to RFC 7807 responses."""

from http import HTTPStatus

from fastapi import Request
from fastapi.responses import JSONResponse
from test_service_server.models.error_details import ErrorDetails

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.entity_not_found_exception import (
    EntityNotFoundException,
)
from test_service.domain.model.exceptions.environment_already_exists_exception import (
    EnvironmentAlreadyExistsException,
)
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin
from test_service.domain.model.exceptions.external_project_not_found_exception import (
    ExternalProjectNotFoundException,
)
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
from test_service.domain.model.exceptions.invalid_project_key_exception import (
    InvalidProjectKeyException,
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
from test_service.domain.model.exceptions.precondition_already_exists_exception import (
    PreconditionAlreadyExistsException,
)
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
from test_service.domain.model.exceptions.test_case_already_exists_exception import (
    TestCaseAlreadyExistsException,
)
from test_service.domain.model.exceptions.test_case_version_already_exists_exception import (
    TestCaseVersionAlreadyExistsException,
)
from test_service.domain.model.exceptions.test_plan_already_exists_exception import (
    TestPlanAlreadyExistsException,
)
from test_service.domain.model.exceptions.test_set_already_exists_exception import (
    TestSetAlreadyExistsException,
)

_GENERIC_SERVER_ERROR_DETAIL = "An unexpected server error occurred."
_GENERIC_PROVIDER_ERROR_DETAIL = "A dependent service error occurred."

_EXCEPTION_STATUS_MAP: dict[type[DomainException], HTTPStatus] = {
    EntityNotFoundException: HTTPStatus.NOT_FOUND,
    ExternalProjectNotFoundException: HTTPStatus.UNPROCESSABLE_ENTITY,
    ProjectAlreadyDeletedException: HTTPStatus.CONFLICT,
    ProjectAlreadyExistsException: HTTPStatus.CONFLICT,
    TestCaseAlreadyExistsException: HTTPStatus.CONFLICT,
    TestCaseVersionAlreadyExistsException: HTTPStatus.CONFLICT,
    TestSetAlreadyExistsException: HTTPStatus.CONFLICT,
    TestPlanAlreadyExistsException: HTTPStatus.CONFLICT,
    PreconditionAlreadyExistsException: HTTPStatus.CONFLICT,
    EnvironmentAlreadyExistsException: HTTPStatus.CONFLICT,
    PreconditionProjectMismatchException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidActionException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidDefinitionException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidEnvironmentTransitionException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidExecutionTransitionException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidLifecycleTransitionException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidPreconditionException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidProjectKeyException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidSecretReferenceException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidTestCaseException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidTestPlanException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidTestSetException: HTTPStatus.UNPROCESSABLE_ENTITY,
    ResolvedSecretNotAllowedException: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidArtifactStorageException: HTTPStatus.BAD_GATEWAY,
    InvalidTemporalDataException: HTTPStatus.BAD_GATEWAY,
    InvalidProjectDeletionException: HTTPStatus.INTERNAL_SERVER_ERROR,
}

# Fallback for domain exception subtypes not yet assigned an HTTP semantic.
_ORIGIN_STATUS_MAP: dict[ErrorOrigin, HTTPStatus] = {
    ErrorOrigin.USER: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorOrigin.INTERNAL: HTTPStatus.INTERNAL_SERVER_ERROR,
    ErrorOrigin.PROVIDER: HTTPStatus.BAD_GATEWAY,
}


def build_problem_response(
    request: Request, http_status: int, title: str, detail: str
) -> JSONResponse:
    """Build an RFC 7807 `ErrorDetails` response."""
    error_details = ErrorDetails(
        status=http_status,
        title=title,
        detail=detail,
        instance=str(request.url),
    )
    return JSONResponse(status_code=http_status, content=error_details.model_dump(by_alias=True))


class ExceptionMapper:
    """Map domain exceptions to client-safe RFC 7807 problem responses."""

    @staticmethod
    def domain_to_problem_response(request: Request, exc: DomainException) -> JSONResponse:
        """Map an expected domain failure to its HTTP problem response."""
        http_status = _EXCEPTION_STATUS_MAP.get(type(exc))

        if http_status is None:
            http_status = _ORIGIN_STATUS_MAP[exc.origin]

        return build_problem_response(
            request,
            http_status,
            http_status.phrase,
            ExceptionMapper._safe_detail(exc),
        )

    @staticmethod
    def _safe_detail(exc: DomainException) -> str:
        """Return client-safe detail without exposing provider or internal failures."""
        if exc.origin is ErrorOrigin.USER:
            return exc.error_description
        if exc.origin is ErrorOrigin.PROVIDER:
            return _GENERIC_PROVIDER_ERROR_DETAIL
        return _GENERIC_SERVER_ERROR_DETAIL
