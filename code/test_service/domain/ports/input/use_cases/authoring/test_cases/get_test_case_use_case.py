"""Input port: get test case."""

from typing import Protocol

from test_service.domain.application.queries.authoring import TestCaseQuery
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.ports.input.use_case import AsyncUseCase


class GetTestCaseUseCase(AsyncUseCase[TestCaseQuery, TestCase], Protocol):
    """Input port for retrieving one TestCase snapshot by UUID."""
