"""Bearer token enforcement and caller identity propagation.

The generated `get_token_bearerAuth` (test_service_server/security_api.py) is an
unimplemented stub and its result is never forwarded to controllers by the
generated router, so token validation must happen independently here, before
the request reaches any controller.
"""

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from test_service.infrastructure.adapters.input.rest.exceptions.exception_mapper import (
    build_problem_response,
)
from test_service.infrastructure.adapters.input.rest.security.identity_context import (
    set_current_identity,
)
from test_service.infrastructure.adapters.input.rest.security.token_validator import (
    InvalidTokenError,
    get_token_validator,
)

_BEARER_PREFIX = "Bearer "
_PUBLIC_PATHS = frozenset({"/docs", "/redoc", "/openapi.json"})


class IdentityMiddleware(BaseHTTPMiddleware):
    """Validates the bearer token and populates the request-scoped identity contextvar."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Reject requests with a missing or invalid bearer token; otherwise propagate identity."""
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith(_BEARER_PREFIX):
            return build_problem_response(
                request, status.HTTP_401_UNAUTHORIZED, "Unauthorized", "A bearer token is required."
            )

        token = authorization[len(_BEARER_PREFIX) :]
        try:
            claims = get_token_validator().get_claims(token)
        except InvalidTokenError as exc:
            return build_problem_response(
                request, status.HTTP_401_UNAUTHORIZED, "Unauthorized", str(exc)
            )

        subject = claims.get("sub")
        set_current_identity(subject if isinstance(subject, str) else None)
        return await call_next(request)
