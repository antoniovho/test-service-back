"""Input port: create precondition."""

from typing import Protocol

from test_service.domain.application.commands.authoring import CreatePreconditionCommand
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.ports.input.use_case import AsyncUseCase


class CreatePreconditionUseCase(AsyncUseCase[CreatePreconditionCommand, Precondition], Protocol):
    """Input port for creating a draft Precondition snapshot."""
