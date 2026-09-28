import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from test_service.adapters.input.rest.error_mapping import register_exception_handlers
from test_service.domain.model.exceptions.domain_exception import (
    BusinessRuleViolationException,
    ConflictException,
    DomainException,
    EntityNotFoundException,
)


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    async def _raise_not_found():
        raise EntityNotFoundException("project", "IAG")

    @app.get("/conflict")
    async def _raise_conflict():
        raise ConflictException("project already exists", "PROJECT_ALREADY_EXISTS")

    @app.get("/business-rule-violation")
    async def _raise_business_rule_violation():
        raise BusinessRuleViolationException(
            "project is already deleted", "PROJECT_ALREADY_DELETED"
        )

    @app.get("/domain-exception")
    async def _raise_domain_exception():
        raise DomainException("generic domain failure", "GENERIC_FAILURE")

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

    def test_when_business_rule_violation_expect_422_problem_details(self, client: TestClient):
        response = client.get("/business-rule-violation")

        assert response.status_code == 422
        assert response.json()["title"] == "Unprocessable Entity"

    def test_when_generic_domain_exception_expect_400_problem_details(self, client: TestClient):
        response = client.get("/domain-exception")

        assert response.status_code == 400
        assert response.json()["title"] == "Bad Request"

    def test_when_unexpected_exception_expect_500_generic_problem_details(self, client: TestClient):
        response = client.get("/unexpected")

        assert response.status_code == 500
        body = response.json()
        assert body["title"] == "Internal Server Error"
        assert body["detail"] == "An unexpected server error occurred."
