"""Input port: deprecate test set."""

from typing import Protocol

from test_service.domain.application.commands.composition import DeprecateTestSetCommand
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.ports.input.use_case import AsyncUseCase


class DeprecateTestSetUseCase(AsyncUseCase[DeprecateTestSetCommand, TestSet], Protocol):
    """Input port for deprecating an active TestSet snapshot."""
