"""Input port: deactivate environment."""

from typing import Protocol

from test_service.domain.application.commands.execution import DeactivateEnvironmentCommand
from test_service.domain.model.execution.environment import Environment
from test_service.domain.ports.input.use_case import AsyncUseCase


class DeactivateEnvironmentUseCase(
    AsyncUseCase[DeactivateEnvironmentCommand, Environment], Protocol
):
    """Input port for marking an environment as unavailable for new executions."""
