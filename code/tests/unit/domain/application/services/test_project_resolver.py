from datetime import UTC, datetime

import pytest

from test_service.domain.application.services.project_resolver import ProjectResolver
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.project_already_deleted_exception import (
    ProjectAlreadyDeletedException,
)
from test_service.domain.model.projects.project import Project


class _ProjectRepository:
    def __init__(self, project: Project | None) -> None:
        self._project = project

    async def find_by_key(self, key: str) -> Project | None:
        return self._project


def _project() -> Project:
    return Project(
        key="IAG",
        name="AI Gateway",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="admin@example.test",
    )


class TestProjectResolver:
    async def test_when_project_exists_expect_resolved_project(self) -> None:
        project = _project()
        resolver = ProjectResolver(_ProjectRepository(project))

        resolved = await resolver.resolve(project.key)

        assert resolved is project

    async def test_when_project_is_missing_expect_not_found_exception(self) -> None:
        resolver = ProjectResolver(_ProjectRepository(None))

        with pytest.raises(EntityNotFoundException) as exception:
            await resolver.resolve("UNKNOWN")

        assert exception.value.code == "ENTITY_NOT_FOUND"

    async def test_when_project_is_active_expect_resolved_active_project(self) -> None:
        project = _project()
        resolver = ProjectResolver(_ProjectRepository(project))

        resolved = await resolver.resolve_active(project.key)

        assert resolved is project

    async def test_when_project_is_deleted_expect_conflict_exception(self) -> None:
        project = _project().delete(datetime(2026, 2, 1, tzinfo=UTC), "admin@example.test")
        resolver = ProjectResolver(_ProjectRepository(project))

        with pytest.raises(ProjectAlreadyDeletedException) as exception:
            await resolver.resolve_active(project.key)

        assert exception.value.code == "PROJECT_ALREADY_DELETED"
