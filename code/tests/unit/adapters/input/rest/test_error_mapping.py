from http import HTTPStatus

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from test_service.adapters.input.rest.handlers.exceptions.exception_handler import (
    _raise_location,
    register_exception_handlers,
)
from test_service.adapters.input.rest.mappers.exceptions.exception_mapper import (
    _EXCEPTION_STATUS_MAP,
)
from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.entity_not_found_exception import (
    EntityNotFoundException,
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


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    async def _raise_not_found():
        raise EntityNotFoundException("project", "IAG")

    @app.get("/conflict")
    async def _raise_conflict():
        raise ProjectAlreadyExistsException("project already exists")

    @app.get("/user-origin")
    async def _raise_user_origin():
        raise InvalidActionException("action type is not allowed")

    @app.get("/provider-origin")
    async def _raise_provider_origin():
        raise InvalidArtifactStorageException("provider storage detail")

    @app.get("/internal-origin")
    async def _raise_internal_origin():
        raise InvalidProjectDeletionException("internal deletion detail")

    @app.get("/unexpected")
    async def _raise_unexpected():
        raise RuntimeError("boom")

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_build_app(), raise_server_exceptions=False)


class TestRegisterExceptionHandlers:
    def test_when_entity_not_found_expect_404_problem_details(self, client: TestClient):
        response = client.get("/not-found")

        assert response.status_code == 404
        body = response.json()
        assert body["status"] == 404
        assert body["title"] == "Not Found"
        assert "IAG" in body["detail"]
        assert body["instance"].endswith("/not-found")

    def test_when_conflict_expect_409_problem_details(self, client: TestClient):
        response = client.get("/conflict")

        assert response.status_code == 409
        assert response.json()["title"] == "Conflict"

    def test_when_user_origin_exception_expect_422_problem_details(self, client: TestClient):
        response = client.get("/user-origin")

        assert response.status_code == 422
        body = response.json()
        assert body["title"] == "Unprocessable Entity"
        assert body["detail"] == "action type is not allowed"

    def test_when_provider_origin_exception_expect_502_generic_problem_details(
        self, client: TestClient
    ):
        response = client.get("/provider-origin")

        body = response.json()
        assert response.status_code == 502
        assert body["title"] == "Bad Gateway"
        assert body["detail"] == "A dependent service error occurred."

    def test_when_internal_origin_exception_expect_500_generic_problem_details(
        self, client: TestClient
    ):
        response = client.get("/internal-origin")

        body = response.json()
        assert response.status_code == 500
        assert body["title"] == "Internal Server Error"
        assert body["detail"] == "An unexpected server error occurred."

    def test_when_unexpected_exception_expect_500_generic_problem_details(self, client: TestClient):
        response = client.get("/unexpected")

        assert response.status_code == 500
        body = response.json()
        assert body["title"] == "Internal Server Error"
        assert body["detail"] == "An unexpected server error occurred."


class TestExceptionStatusMap:
    def test_when_domain_exception_has_http_semantic_expect_explicit_status_mapping(self):
        expected_status_map = {
            EntityNotFoundException: HTTPStatus.NOT_FOUND,
            ProjectAlreadyDeletedException: HTTPStatus.CONFLICT,
            ProjectAlreadyExistsException: HTTPStatus.CONFLICT,
            PreconditionProjectMismatchException: HTTPStatus.UNPROCESSABLE_ENTITY,
            InvalidActionException: HTTPStatus.UNPROCESSABLE_ENTITY,
            InvalidDefinitionException: HTTPStatus.UNPROCESSABLE_ENTITY,
            InvalidEnvironmentTransitionException: HTTPStatus.UNPROCESSABLE_ENTITY,
            InvalidExecutionTransitionException: HTTPStatus.UNPROCESSABLE_ENTITY,
            InvalidLifecycleTransitionException: HTTPStatus.UNPROCESSABLE_ENTITY,
            InvalidPreconditionException: HTTPStatus.UNPROCESSABLE_ENTITY,
            InvalidSecretReferenceException: HTTPStatus.UNPROCESSABLE_ENTITY,
            InvalidTestCaseException: HTTPStatus.UNPROCESSABLE_ENTITY,
            InvalidTestPlanException: HTTPStatus.UNPROCESSABLE_ENTITY,
            InvalidTestSetException: HTTPStatus.UNPROCESSABLE_ENTITY,
            ResolvedSecretNotAllowedException: HTTPStatus.UNPROCESSABLE_ENTITY,
            InvalidArtifactStorageException: HTTPStatus.BAD_GATEWAY,
            InvalidTemporalDataException: HTTPStatus.BAD_GATEWAY,
            InvalidProjectDeletionException: HTTPStatus.INTERNAL_SERVER_ERROR,
        }

        actual_status_map = _EXCEPTION_STATUS_MAP

        assert actual_status_map == expected_status_map


class TestRaiseLocation:
    def test_when_exception_has_no_traceback_expect_module_name(self):
        exc = InvalidActionException("never raised")

        assert (
            _raise_location(exc) == "test_service.domain.model.exceptions.invalid_action_exception"
        )

    def test_when_exception_was_raised_expect_module_and_line(self):
        try:
            raise InvalidActionException("boom")
        except DomainException as exc:
            location = _raise_location(exc)

        assert location.startswith(f"{__name__}:")
