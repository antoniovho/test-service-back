"""Input port: get test plan."""

from typing import Protocol

from test_service.domain.application.queries.composition import TestPlanQuery
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.ports.input.use_case import AsyncUseCase


class GetTestPlanUseCase(AsyncUseCase[TestPlanQuery, TestPlan], Protocol):
    """Input port for retrieving one TestPlan snapshot by UUID."""
