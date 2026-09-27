"""Input port: activate test set."""

from typing import Protocol

from test_service.domain.application.commands.composition import ActivateTestSetCommand
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.ports.input.use_case import AsyncUseCase


class ActivateTestSetUseCase(AsyncUseCase[ActivateTestSetCommand, TestSet], Protocol):
    """Input port for activating a draft TestSet snapshot."""
