"""Input port: list preconditions across a project."""

from typing import Protocol

from test_service.domain.application.queries.authoring import ListPreconditionsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListPreconditionsUseCase(AsyncUseCase[ListPreconditionsQuery, Page[Precondition]], Protocol):
    """Input port for listing Precondition snapshots owned by a project."""
