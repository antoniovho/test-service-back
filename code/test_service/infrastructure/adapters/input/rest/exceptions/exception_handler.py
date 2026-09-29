"""FastAPI handlers for expected and unexpected exceptions."""

import logging
from types import TracebackType

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.infrastructure.adapters.input.rest.exceptions.exception_mapper import (
    ExceptionMapper,
    build_problem_response,
)

logger = logging.getLogger(__name__)
_GENERIC_SERVER_ERROR_DETAIL = "An unexpected server error occurred."


def _raise_location(exc: BaseException) -> str:
    """Return `module:line` where the exception was raised, for log correlation."""
    traceback: TracebackType | None = exc.__traceback__
    if traceback is None:
        return type(exc).__module__
    while traceback.tb_next is not None:
        traceback = traceback.tb_next
    module = traceback.tb_frame.f_globals.get("__name__", "unknown")
    return f"{module}:{traceback.tb_lineno}"


class ExceptionHandler:
    """Handle REST exceptions using an injected domain exception mapper."""

    def __init__(self, exception_mapper: ExceptionMapper) -> None:
        self._exception_mapper = exception_mapper

    def domain_exception_handler(self, request: Request, exc: Exception) -> JSONResponse:
        """Translate an expected domain exception into a client-safe problem response."""
        assert isinstance(exc, DomainException)
        logger.info(
            "[%s][%s] %s | raised at %s",
            exc.code,
            exc.origin.value,
            exc.error_description,
            _raise_location(exc),
        )
        return self._exception_mapper.domain_to_problem_response(request, exc)

    def unexpected_exception_handler(self, request: Request, exc: Exception) -> JSONResponse:
        """Translate unexpected exceptions without exposing internal details."""
        logger.error("Unhandled exception raised at %s", _raise_location(exc), exc_info=exc)
        return build_problem_response(
            request,
            http_status=500,
            title="Internal Server Error",
            detail=_GENERIC_SERVER_ERROR_DETAIL,
        )


def register_exception_handlers(
    app: FastAPI, exception_handler: ExceptionHandler | None = None
) -> None:
    """Register the REST exception handlers for the application."""
    handler = exception_handler or ExceptionHandler(ExceptionMapper())
    app.add_exception_handler(DomainException, handler.domain_exception_handler)
    app.add_exception_handler(Exception, handler.unexpected_exception_handler)
