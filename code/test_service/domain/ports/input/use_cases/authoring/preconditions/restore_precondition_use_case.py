"""Input port: restore a historical Precondition snapshot."""

from typing import Protocol

from test_service.domain.application.commands.authoring import RestorePreconditionCommand
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.ports.input.use_case import AsyncUseCase


class RestorePreconditionUseCase(AsyncUseCase[RestorePreconditionCommand, Precondition], Protocol):
    """Clone a deprecated Precondition snapshot into the next draft version."""
