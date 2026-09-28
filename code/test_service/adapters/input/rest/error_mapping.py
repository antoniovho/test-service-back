"""Global mapping from domain exceptions to RFC 7807 problem responses."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from test_service_server.models.error_details import ErrorDetails

from test_service.domain.model.exceptions.domain_exception import (
    BusinessRuleViolationException,
    ConflictException,
    DomainException,
    EntityNotFoundException,
)

_GENERIC_SERVER_ERROR_DETAIL = "An unexpected server error occurred."


def build_problem_response(
    request: Request, http_status: int, title: str, detail: str
) -> JSONResponse:
    """Build an RFC 7807 `ErrorDetails` response, shared by exception handlers and middlewares."""
    error_details = ErrorDetails(
        status=http_status,
        title=title,
        detail=detail,
        instance=str(request.url),
    )
    return JSONResponse(status_code=http_status, content=error_details.model_dump(by_alias=True))


def register_exception_handlers(app: FastAPI) -> None:
    """Register handlers translating domain exceptions into `ErrorDetails` responses."""

    @app.exception_handler(EntityNotFoundException)
    async def _handle_not_found(request: Request, exc: EntityNotFoundException) -> JSONResponse:
        return build_problem_response(request, status.HTTP_404_NOT_FOUND, "Not Found", str(exc))

    @app.exception_handler(ConflictException)
    async def _handle_conflict(request: Request, exc: ConflictException) -> JSONResponse:
        return build_problem_response(request, status.HTTP_409_CONFLICT, "Conflict", str(exc))

    @app.exception_handler(BusinessRuleViolationException)
    async def _handle_business_rule_violation(
        request: Request, exc: BusinessRuleViolationException
    ) -> JSONResponse:
        return build_problem_response(
            request, status.HTTP_422_UNPROCESSABLE_ENTITY, "Unprocessable Entity", str(exc)
        )

    @app.exception_handler(DomainException)
    async def _handle_domain_exception(request: Request, exc: DomainException) -> JSONResponse:
        return build_problem_response(request, status.HTTP_400_BAD_REQUEST, "Bad Request", str(exc))

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return build_problem_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            _GENERIC_SERVER_ERROR_DETAIL,
        )
