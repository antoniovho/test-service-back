"""Input port: get environment."""

from typing import Protocol

from test_service.domain.application.queries.execution import EnvironmentQuery
from test_service.domain.model.execution.environment import Environment
from test_service.domain.ports.input.use_case import AsyncUseCase


class GetEnvironmentUseCase(AsyncUseCase[EnvironmentQuery, Environment], Protocol):
    """Input port for retrieving one environment by UUID."""
