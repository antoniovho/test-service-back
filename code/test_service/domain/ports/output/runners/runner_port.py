"""Contract implemented by replaceable automated-test runners."""

import asyncio
from typing import Protocol

from test_service.domain.ports.output.runners.runner_dtos import (
    CompiledTestCase,
    RunnerTestCaseOutcome,
)


class RunnerPort(Protocol):
    """Execute already compiled test cases and honour cooperative cancellation."""

    @property
    def identifier(self) -> str:
        """Stable runner identifier."""
        ...

    @property
    def version(self) -> str:
        """Runner implementation version."""
        ...

    def supports(self, action_types: frozenset[str]) -> bool:
        """Report whether every requested action can be executed."""
        ...

    async def execute(
        self, test_case: CompiledTestCase, cancellation: asyncio.Event
    ) -> RunnerTestCaseOutcome:
        """Execute a test case and return safe normalized outcomes."""
        ...
