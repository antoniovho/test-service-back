"""Input port: activate precondition."""

from typing import Protocol

from test_service.domain.application.commands.authoring import ActivatePreconditionCommand
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.ports.input.use_case import AsyncUseCase


class ActivatePreconditionUseCase(
    AsyncUseCase[ActivatePreconditionCommand, Precondition], Protocol
):
    """Input port for activating a draft Precondition snapshot."""
