"""Input port: delete project."""

from typing import Protocol

from test_service.domain.application.commands.projects import DeleteProjectCommand
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_case import AsyncUseCase


class DeleteProjectUseCase(AsyncUseCase[DeleteProjectCommand, Project], Protocol):
    """Input port for logically deleting one Project Catalog entry."""
