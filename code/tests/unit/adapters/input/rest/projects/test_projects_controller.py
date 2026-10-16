"""Tests for the Project Catalog REST controller."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from test_service.domain.model.projects.project import Project, ProjectStatus
from test_service.infrastructure.adapters.input.rest.projects.projects_controller import (
    ProjectsController,
)


class TestProjectsController:
    async def test_when_restoring_project_expect_restore_command_and_active_response(
        self, monkeypatch
    ):
        restored = Project(
            key="IAG",
            name="AI Gateway",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="creator@example.com",
            status=ProjectStatus.ACTIVE,
        )
        restore_use_case = SimpleNamespace(execute=AsyncMock(return_value=restored))
        controller = ProjectsController.__new__(ProjectsController)
        controller._restore_project_use_case = restore_use_case
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.projects.projects_controller."
            "get_current_identity",
            lambda: "restorer@example.com",
        )

        response = await controller.restore_project("IAG")

        command = restore_use_case.execute.await_args.args[0]
        assert command.key == "IAG"
        assert command.requested_by == "restorer@example.com"
        assert response.key == "IAG"
        assert response.status == "ACTIVE"
