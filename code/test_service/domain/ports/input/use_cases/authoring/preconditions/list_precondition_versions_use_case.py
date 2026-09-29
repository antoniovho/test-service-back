"""Input port: list precondition versions sharing a key."""

from typing import Protocol

from test_service.domain.application.queries.authoring import PreconditionVersionsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListPreconditionVersionsUseCase(
    AsyncUseCase[PreconditionVersionsQuery, Page[Precondition]], Protocol
):
    """Input port for listing versions sharing a Precondition key."""
