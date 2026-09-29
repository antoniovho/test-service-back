"""Input port: create precondition version."""

from typing import Protocol

from test_service.domain.application.commands.authoring import (
    CreatePreconditionVersionCommand,
)
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.ports.input.use_case import AsyncUseCase


class CreatePreconditionVersionUseCase(
    AsyncUseCase[CreatePreconditionVersionCommand, Precondition], Protocol
):
    """Input port for creating a new Precondition version from an existing snapshot."""
