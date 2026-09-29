"""Input port: list action results for a test result."""

from typing import Protocol

from test_service.domain.application.queries.execution import ListExecutionResultActionsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.execution import ActionResult
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListExecutionResultActionsUseCase(
    AsyncUseCase[ListExecutionResultActionsQuery, Page[ActionResult]], Protocol
):
    """Input port for listing action results recorded for one test result."""
