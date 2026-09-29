"""Input port: deprecate test plan."""

from typing import Protocol

from test_service.domain.application.commands.composition import DeprecateTestPlanCommand
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.ports.input.use_case import AsyncUseCase


class DeprecateTestPlanUseCase(AsyncUseCase[DeprecateTestPlanCommand, TestPlan], Protocol):
    """Input port for deprecating an active TestPlan snapshot."""
