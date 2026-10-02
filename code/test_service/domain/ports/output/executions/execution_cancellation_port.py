"""Manage cooperative cancellation for executions owned by this process."""

import asyncio
from typing import Protocol
from uuid import UUID


class ExecutionCancellationPort(Protocol):
    """Manage cancellation signals for running executions."""

    def register(self, execution_id: UUID) -> asyncio.Event:
        """Register a cancellation signal for an execution."""
        ...

    def unregister(self, execution_id: UUID) -> None:
        """Remove the cancellation signal for an execution."""
        ...

    def request_cancellation(self, execution_id: UUID) -> None:
        """Signal cancellation for an execution currently owned by this process."""
        ...
