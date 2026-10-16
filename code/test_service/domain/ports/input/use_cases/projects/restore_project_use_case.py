"""Input port: restore project."""

from typing import Protocol

from test_service.domain.application.commands.projects import RestoreProjectCommand
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_case import AsyncUseCase


class RestoreProjectUseCase(AsyncUseCase[RestoreProjectCommand, Project], Protocol):
    """Input port for restoring a logically deleted project."""
