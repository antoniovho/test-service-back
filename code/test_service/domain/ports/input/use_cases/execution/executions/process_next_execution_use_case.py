"""Input port for processing the next queued execution."""

from typing import Protocol

from test_service.domain.model.execution.execution import Execution
from test_service.domain.ports.input.use_case import AsyncUseCase


class ProcessNextExecutionUseCase(AsyncUseCase[None, Execution | None], Protocol):
    """Process the next queued execution, if one exists."""

    async def execute(self, request: None) -> Execution | None:
        """Claim and process the next queued execution."""
        ...
