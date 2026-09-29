"""Input port: list test case versions sharing a key."""

from typing import Protocol

from test_service.domain.application.queries.authoring import TestCaseVersionsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListTestCaseVersionsUseCase(AsyncUseCase[TestCaseVersionsQuery, Page[TestCase]], Protocol):
    """Input port for listing versions sharing a TestCase key."""
