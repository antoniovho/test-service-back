"""Input port: create test plan version."""

from typing import Protocol

from test_service.domain.application.commands.composition import CreateTestPlanVersionCommand
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.ports.input.use_case import AsyncUseCase


class CreateTestPlanVersionUseCase(AsyncUseCase[CreateTestPlanVersionCommand, TestPlan], Protocol):
    """Input port for creating a new TestPlan version from an existing snapshot."""
