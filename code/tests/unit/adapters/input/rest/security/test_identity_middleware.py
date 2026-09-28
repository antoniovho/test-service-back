import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from test_service.adapters.input.rest.security.identity_context import get_current_identity
from test_service.adapters.input.rest.security.identity_middleware import IdentityMiddleware
from test_service.adapters.input.rest.security.token_validator import get_token_validator


async def _whoami(request):
    return JSONResponse({"identity": get_current_identity()})


def _build_app() -> Starlette:
    app = Starlette(routes=[Route("/whoami", _whoami), Route("/docs", _whoami)])
    app.add_middleware(IdentityMiddleware)
    return app


@pytest.fixture(autouse=True)
def _clear_validator_cache(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_MOCK_ENABLED", "true")
    get_token_validator.cache_clear()
    yield
    get_token_validator.cache_clear()


class TestIdentityMiddleware:
    def test_when_no_authorization_header_expect_401(self):
        client = TestClient(_build_app())

        response = client.get("/whoami")

        assert response.status_code == 401
        assert response.json()["title"] == "Unauthorized"

    def test_when_bearer_token_present_expect_identity_propagated(self):
        client = TestClient(_build_app())

        response = client.get(
            "/whoami", headers={"Authorization": "Bearer x.eyJzdWIiOiJhbGljZUBleGFtcGxlLmNvbSJ9.y"}
        )

        assert response.status_code == 200
        assert response.json()["identity"] == "alice@example.com"

    def test_when_public_path_expect_no_authorization_required(self):
        client = TestClient(_build_app())

        response = client.get("/docs")

        assert response.status_code == 200
