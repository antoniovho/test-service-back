"""Input port: get one execution result."""

from typing import Protocol

from test_service.domain.application.queries.execution import ExecutionResultQuery
from test_service.domain.model.execution.execution import TestResult
from test_service.domain.ports.input.use_case import AsyncUseCase


class GetExecutionResultUseCase(AsyncUseCase[ExecutionResultQuery, TestResult], Protocol):
    """Input port for retrieving one immutable test result belonging to an execution."""
