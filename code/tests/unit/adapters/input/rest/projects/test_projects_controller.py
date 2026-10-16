"""Tests for the Project Catalog REST controller."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from test_service.domain.model.projects.project import Project, ProjectStatus
from test_service.infrastructure.adapters.input.rest.projects.projects_controller import (
    ProjectsController,
)


class TestProjectsController:
    def test_when_constructed_expect_all_project_use_cases_injected(self, monkeypatch) -> None:
        injector = MagicMock()
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.projects.projects_controller.get_injector",
            lambda: injector,
        )

        controller = ProjectsController()

        assert controller._list_projects_use_case is injector.inject.return_value
        assert injector.inject.call_count == 5

    async def test_when_project_endpoints_are_called_expect_use_cases_and_mappers_used(
        self, monkeypatch
    ) -> None:
        controller = ProjectsController.__new__(ProjectsController)
        controller._list_projects_use_case = MagicMock(execute=AsyncMock(return_value="page"))
        controller._create_project_use_case = MagicMock(execute=AsyncMock(return_value="created"))
        controller._get_project_use_case = MagicMock(execute=AsyncMock(return_value="found"))
        controller._delete_project_use_case = MagicMock(execute=AsyncMock())
        controller._restore_project_use_case = MagicMock(execute=AsyncMock(return_value="restored"))
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.projects.projects_controller."
            "get_current_identity",
            lambda: "author@example.test",
        )
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.projects.projects_controller."
            "ProjectMapper.to_pagination_params",
            lambda *_: "pagination",
        )
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.projects.projects_controller."
            "ProjectMapper.to_list_query",
            lambda *_: "list-query",
        )
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.projects.projects_controller."
            "ProjectMapper.domain_page_to_list_response",
            lambda *_: "list-response",
        )
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.projects.projects_controller."
            "ProjectMapper.to_create_command",
            lambda *_: "create-command",
        )
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.projects.projects_controller."
            "ProjectMapper.to_get_query",
            lambda _: "get-query",
        )
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.projects.projects_controller."
            "ProjectMapper.to_delete_command",
            lambda *_: "delete-command",
        )
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.projects.projects_controller."
            "ProjectMapper.to_restore_command",
            lambda *_: "restore-command",
        )
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.projects.projects_controller."
            "ProjectMapper.domain_to_api",
            lambda project: f"api-{project}",
        )

        assert await controller.list_projects(0, 20, None, None, "DELETED") == "list-response"
        assert await controller.create_project(MagicMock()) == "api-created"
        assert await controller.get_project("IAG") == "api-found"
        assert await controller.delete_project("IAG") is None

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
