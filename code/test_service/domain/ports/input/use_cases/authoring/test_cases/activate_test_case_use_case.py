"""Input port: activate test case."""

from typing import Protocol

from test_service.domain.application.commands.authoring import ActivateTestCaseCommand
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.ports.input.use_case import AsyncUseCase


class ActivateTestCaseUseCase(AsyncUseCase[ActivateTestCaseCommand, TestCase], Protocol):
    """Input port for activating a draft TestCase snapshot."""
