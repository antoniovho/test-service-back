"""Input port: restore a historical Test Case snapshot."""

from typing import Protocol

from test_service.domain.application.commands.authoring import RestoreTestCaseCommand
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.ports.input.use_case import AsyncUseCase


class RestoreTestCaseUseCase(AsyncUseCase[RestoreTestCaseCommand, TestCase], Protocol):
    """Clone a deprecated Test Case snapshot into the next draft version."""
