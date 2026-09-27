"""Input port: list test plan versions sharing a key."""

from typing import Protocol

from test_service.domain.application.queries.composition import ListTestPlanVersionsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListTestPlanVersionsUseCase(
    AsyncUseCase[ListTestPlanVersionsQuery, Page[TestPlan]], Protocol
):
    """Input port for listing versions sharing a TestPlan key."""
