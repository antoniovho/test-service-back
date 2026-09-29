"""Input port: create project."""

from typing import Protocol

from test_service.domain.application.commands.projects import CreateProjectCommand
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_case import AsyncUseCase


class CreateProjectUseCase(AsyncUseCase[CreateProjectCommand, Project], Protocol):
    """Input port for registering a validated project."""
