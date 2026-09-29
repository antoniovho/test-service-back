"""Input port: deprecate precondition."""

from typing import Protocol

from test_service.domain.application.commands.authoring import DeprecatePreconditionCommand
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.ports.input.use_case import AsyncUseCase


class DeprecatePreconditionUseCase(
    AsyncUseCase[DeprecatePreconditionCommand, Precondition], Protocol
):
    """Input port for deprecating an active Precondition snapshot."""
