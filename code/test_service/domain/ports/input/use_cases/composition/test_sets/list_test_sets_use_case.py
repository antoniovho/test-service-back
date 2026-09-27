"""Input port: list test set versions across a project."""

from typing import Protocol

from test_service.domain.application.queries.composition import ListTestSetsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListTestSetsUseCase(AsyncUseCase[ListTestSetsQuery, Page[TestSet]], Protocol):
    """Input port for listing TestSet snapshots owned by a project."""
