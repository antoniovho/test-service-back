"""Input port: create test case version."""

from typing import Protocol

from test_service.domain.application.commands.authoring import CreateTestCaseVersionCommand
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.ports.input.use_case import AsyncUseCase


class CreateTestCaseVersionUseCase(AsyncUseCase[CreateTestCaseVersionCommand, TestCase], Protocol):
    """Input port for creating a new TestCase version from an existing snapshot."""
