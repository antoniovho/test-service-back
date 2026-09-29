"""Input port: list test set versions sharing a key."""

from typing import Protocol

from test_service.domain.application.queries.composition import ListTestSetVersionsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListTestSetVersionsUseCase(AsyncUseCase[ListTestSetVersionsQuery, Page[TestSet]], Protocol):
    """Input port for listing versions sharing a TestSet key."""
