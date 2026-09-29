"""Input port: list projects."""

from typing import Protocol

from test_service.domain.application.queries.projects import ListProjectsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListProjectsUseCase(AsyncUseCase[ListProjectsQuery, Page[Project]], Protocol):
    """Input port for listing Project Catalog entries."""
