"""Input port: get precondition."""

from typing import Protocol

from test_service.domain.application.queries.authoring import PreconditionQuery
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.ports.input.use_case import AsyncUseCase


class GetPreconditionUseCase(AsyncUseCase[PreconditionQuery, Precondition], Protocol):
    """Input port for retrieving one Precondition snapshot by UUID."""
