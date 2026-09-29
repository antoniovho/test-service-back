"""Input port: get execution."""

from typing import Protocol

from test_service.domain.application.queries.execution import ExecutionQuery
from test_service.domain.model.execution.execution import Execution
from test_service.domain.ports.input.use_case import AsyncUseCase


class GetExecutionUseCase(AsyncUseCase[ExecutionQuery, Execution], Protocol):
    """Input port for retrieving one execution by UUID."""
