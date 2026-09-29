"""Input port: list executions."""

from typing import Protocol

from test_service.domain.application.queries.execution import ListExecutionsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.execution import Execution
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListExecutionsUseCase(AsyncUseCase[ListExecutionsQuery, Page[Execution]], Protocol):
    """Input port for listing executions owned by a project."""
