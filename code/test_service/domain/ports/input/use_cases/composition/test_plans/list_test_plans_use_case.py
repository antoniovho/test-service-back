"""Input port: list test plan versions across a project."""

from typing import Protocol

from test_service.domain.application.queries.composition import ListTestPlansQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListTestPlansUseCase(AsyncUseCase[ListTestPlansQuery, Page[TestPlan]], Protocol):
    """Input port for listing TestPlan snapshots owned by a project."""
