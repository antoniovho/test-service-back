"""Input port: create test set."""

from typing import Protocol

from test_service.domain.application.commands.composition import CreateTestSetCommand
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.ports.input.use_case import AsyncUseCase


class CreateTestSetUseCase(AsyncUseCase[CreateTestSetCommand, TestSet], Protocol):
    """Input port for creating a draft TestSet snapshot."""
