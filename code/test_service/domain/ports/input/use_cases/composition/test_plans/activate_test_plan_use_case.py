"""Input port: activate test plan."""

from typing import Protocol

from test_service.domain.application.commands.composition import ActivateTestPlanCommand
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.ports.input.use_case import AsyncUseCase


class ActivateTestPlanUseCase(AsyncUseCase[ActivateTestPlanCommand, TestPlan], Protocol):
    """Input port for activating a draft TestPlan snapshot."""
