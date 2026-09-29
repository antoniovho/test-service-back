"""Input port: create environment."""

from typing import Protocol

from test_service.domain.application.commands.execution import CreateEnvironmentCommand
from test_service.domain.model.execution.environment import Environment
from test_service.domain.ports.input.use_case import AsyncUseCase


class CreateEnvironmentUseCase(AsyncUseCase[CreateEnvironmentCommand, Environment], Protocol):
    """Input port for creating execution environment metadata."""
