"""Input port: activate environment."""

from typing import Protocol

from test_service.domain.application.commands.execution import ActivateEnvironmentCommand
from test_service.domain.model.execution.environment import Environment
from test_service.domain.ports.input.use_case import AsyncUseCase


class ActivateEnvironmentUseCase(AsyncUseCase[ActivateEnvironmentCommand, Environment], Protocol):
    """Input port for marking an environment as available for new executions."""
