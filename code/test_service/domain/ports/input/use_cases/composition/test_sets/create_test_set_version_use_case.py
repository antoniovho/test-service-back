"""Input port: create test set version."""

from typing import Protocol

from test_service.domain.application.commands.composition import CreateTestSetVersionCommand
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.ports.input.use_case import AsyncUseCase


class CreateTestSetVersionUseCase(AsyncUseCase[CreateTestSetVersionCommand, TestSet], Protocol):
    """Input port for creating a new TestSet version from an existing snapshot."""
