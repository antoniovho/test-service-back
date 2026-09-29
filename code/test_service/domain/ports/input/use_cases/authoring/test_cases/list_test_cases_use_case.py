"""Input port: list test case versions across a project."""

from typing import Protocol

from test_service.domain.application.queries.authoring import ListTestCasesQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListTestCasesUseCase(AsyncUseCase[ListTestCasesQuery, Page[TestCase]], Protocol):
    """Input port for listing TestCase snapshots owned by a project."""
