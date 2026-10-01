"""In-process registry for cooperative execution cancellation."""

import asyncio
from uuid import UUID

from test_service.domain.ports.output.executions.execution_cancellation_port import (
    ExecutionCancellationPort,
)


class ExecutionCancellationRegistry(ExecutionCancellationPort):
    """Store cancellation signals for executions running in this process."""

    def __init__(self) -> None:
        self._events: dict[UUID, asyncio.Event] = {}

    def register(self, execution_id: UUID) -> asyncio.Event:
        """Return the signal used by a claimed execution."""
        event = asyncio.Event()
        self._events[execution_id] = event
        return event

    def unregister(self, execution_id: UUID) -> None:
        """Remove the completed execution control channel."""
        self._events.pop(execution_id, None)

    def request_cancellation(self, execution_id: UUID) -> None:
        """Signal the in-flight runner, if this process owns it."""
        event = self._events.get(execution_id)
        if event is not None:
            event.set()
