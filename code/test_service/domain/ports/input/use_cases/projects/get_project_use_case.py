"""Input port: get project."""

from typing import Protocol

from test_service.domain.application.queries.projects import GetProjectQuery
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_case import AsyncUseCase


class GetProjectUseCase(AsyncUseCase[GetProjectQuery, Project], Protocol):
    """Input port for retrieving one Project Catalog entry."""
