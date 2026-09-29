"""Input port: create test plan."""

from typing import Protocol

from test_service.domain.application.commands.composition import CreateTestPlanCommand
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.ports.input.use_case import AsyncUseCase


class CreateTestPlanUseCase(AsyncUseCase[CreateTestPlanCommand, TestPlan], Protocol):
    """Input port for creating a draft TestPlan snapshot."""
