"""Input port: restore a historical Test Set snapshot."""

from typing import Protocol

from test_service.domain.application.commands.composition import RestoreTestSetCommand
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.ports.input.use_case import AsyncUseCase


class RestoreTestSetUseCase(AsyncUseCase[RestoreTestSetCommand, TestSet], Protocol):
    """Clone a deprecated Test Set snapshot into the next draft version."""
