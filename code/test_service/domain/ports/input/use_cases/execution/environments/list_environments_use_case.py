"""Input port: list environments."""

from typing import Protocol

from test_service.domain.application.queries.execution import ListEnvironmentsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.environment import Environment
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListEnvironmentsUseCase(AsyncUseCase[ListEnvironmentsQuery, Page[Environment]], Protocol):
    """Input port for listing execution environments."""
