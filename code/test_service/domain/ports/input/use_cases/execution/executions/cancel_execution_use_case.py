"""Input port: cancel execution."""

from typing import Protocol

from test_service.domain.application.commands.execution import CancelExecutionCommand
from test_service.domain.model.execution.execution import Execution
from test_service.domain.ports.input.use_case import AsyncUseCase


class CancelExecutionUseCase(AsyncUseCase[CancelExecutionCommand, Execution], Protocol):
    """Input port for cancelling an execution that has not reached a terminal state."""
