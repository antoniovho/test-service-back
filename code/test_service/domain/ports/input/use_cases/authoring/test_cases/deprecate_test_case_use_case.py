"""Input port: deprecate test case."""

from typing import Protocol

from test_service.domain.application.commands.authoring import DeprecateTestCaseCommand
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.ports.input.use_case import AsyncUseCase


class DeprecateTestCaseUseCase(AsyncUseCase[DeprecateTestCaseCommand, TestCase], Protocol):
    """Input port for deprecating an active TestCase snapshot."""
