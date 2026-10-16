"""Input port: restore a historical Test Plan snapshot."""

from typing import Protocol

from test_service.domain.application.commands.composition import RestoreTestPlanCommand
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.ports.input.use_case import AsyncUseCase


class RestoreTestPlanUseCase(AsyncUseCase[RestoreTestPlanCommand, TestPlan], Protocol):
    """Clone a deprecated Test Plan snapshot into the next draft version."""
