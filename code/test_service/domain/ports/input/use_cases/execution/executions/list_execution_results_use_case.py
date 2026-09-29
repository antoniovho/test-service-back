"""Input port: list results for an execution."""

from typing import Protocol

from test_service.domain.application.queries.execution import ListExecutionResultsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.execution import TestResult
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListExecutionResultsUseCase(
    AsyncUseCase[ListExecutionResultsQuery, Page[TestResult]], Protocol
):
    """Input port for listing test results recorded for an execution."""
