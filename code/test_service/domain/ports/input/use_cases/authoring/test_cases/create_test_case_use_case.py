"""Input port: create test case."""

from typing import Protocol

from test_service.domain.application.commands.authoring import CreateTestCaseCommand
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.ports.input.use_case import AsyncUseCase


class CreateTestCaseUseCase(AsyncUseCase[CreateTestCaseCommand, TestCase], Protocol):
    """Input port for creating a draft TestCase snapshot."""
