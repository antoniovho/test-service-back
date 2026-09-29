"""Input port: schedule execution."""

from typing import Protocol

from test_service.domain.application.commands.execution import ScheduleExecutionCommand
from test_service.domain.model.execution.execution import Execution
from test_service.domain.ports.input.use_case import AsyncUseCase


class ScheduleExecutionUseCase(AsyncUseCase[ScheduleExecutionCommand, Execution], Protocol):
    """Input port for scheduling an execution of exact plan and environment snapshots."""
