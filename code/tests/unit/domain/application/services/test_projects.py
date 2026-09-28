from datetime import UTC, datetime
from uuid import uuid4

import pytest

from test_service.domain.application.commands.projects import (
    CreateProjectCommand,
    DeleteProjectCommand,
)
from test_service.domain.application.queries.projects import GetProjectQuery, ListProjectsQuery
from test_service.domain.application.use_cases.projects.create_project_use_case import (
    CreateProjectUseCaseImpl,
)
from test_service.domain.application.use_cases.projects.delete_project_use_case import (
    DeleteProjectUseCaseImpl,
)
from test_service.domain.application.use_cases.projects.get_project_use_case import (
    GetProjectUseCaseImpl,
)
from test_service.domain.application.use_cases.projects.list_projects_use_case import (
    ListProjectsUseCaseImpl,
)
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.exceptions.entity_not_found_exception import (
    EntityNotFoundException,
)
from test_service.domain.model.exceptions.project_already_deleted_exception import (
    ProjectAlreadyDeletedException,
)
from test_service.domain.model.exceptions.project_already_exists_exception import (
    ProjectAlreadyExistsException,
)
from test_service.domain.model.projects.project import Project, ProjectStatus


class InMemoryProjectRepository:
    def __init__(self, projects: tuple[Project, ...] = ()) -> None:
        self._projects_by_key = {project.key: project for project in projects}

    async def save(self, project: Project) -> Project:
        self._projects_by_key[project.key] = project
        return project

    async def find_by_key(self, key: str) -> Project | None:
        return self._projects_by_key.get(key)

    async def find_page(self, pagination: PaginationParams) -> Page[Project]:
        projects = tuple(self._projects_by_key.values())
        page_items = projects[pagination.offset : pagination.offset + pagination.limit]
        return Page(items=page_items, total=len(projects))


def _project(**overrides: object) -> Project:
    fields = {
        "key": "IAG",
        "name": "AI Gateway",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": "admin@example.com",
    }
    fields.update(overrides)
    return Project(**fields)


class TestListProjectsUseCaseImpl:
    async def test_when_projects_exist_expect_page_from_repository(self):
        project = _project()
        use_case = ListProjectsUseCaseImpl(InMemoryProjectRepository((project,)))

        page = await use_case.execute(ListProjectsQuery(pagination=PaginationParams()))

        assert page.items == (project,)
        assert page.total == 1


class TestCreateProjectUseCaseImpl:
    async def test_when_key_is_unused_expect_project_persisted(self):
        use_case = CreateProjectUseCaseImpl(InMemoryProjectRepository())
        requested_at = datetime(2026, 1, 1, tzinfo=UTC)

        project = await use_case.execute(
            CreateProjectCommand(
                key="IAG",
                name="AI Gateway",
                requested_by="admin@example.com",
                requested_at=requested_at,
            )
        )

        assert project.key == "IAG"
        assert project.name == "AI Gateway"
        assert project.created_by == "admin@example.com"
        assert project.created_at == requested_at
        assert project.status is ProjectStatus.ACTIVE

    async def test_when_key_already_exists_expect_already_exists_exception(self):
        existing = _project()
        use_case = CreateProjectUseCaseImpl(InMemoryProjectRepository((existing,)))
        request = CreateProjectCommand(
            key=existing.key,
            name="Another name",
            requested_by="admin@example.com",
            requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        with pytest.raises(ProjectAlreadyExistsException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "PROJECT_ALREADY_EXISTS"


class TestGetProjectUseCaseImpl:
    async def test_when_project_exists_expect_project_returned(self):
        project = _project()
        use_case = GetProjectUseCaseImpl(InMemoryProjectRepository((project,)))

        result = await use_case.execute(GetProjectQuery(key=project.key))

        assert result == project

    async def test_when_project_does_not_exist_expect_not_found_exception(self):
        use_case = GetProjectUseCaseImpl(InMemoryProjectRepository())
        request = GetProjectQuery(key="UNKNOWN")

        with pytest.raises(EntityNotFoundException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "ENTITY_NOT_FOUND"


class TestDeleteProjectUseCaseImpl:
    async def test_when_project_exists_expect_project_marked_deleted(self):
        project = _project()
        repository = InMemoryProjectRepository((project,))
        use_case = DeleteProjectUseCaseImpl(repository)
        requested_at = datetime(2026, 2, 1, tzinfo=UTC)

        deleted_project = await use_case.execute(
            DeleteProjectCommand(
                key=project.key, requested_by="admin@example.com", requested_at=requested_at
            )
        )

        assert deleted_project.status is ProjectStatus.DELETED
        assert deleted_project.deleted_at == requested_at
        assert deleted_project.deleted_by == "admin@example.com"
        assert (await repository.find_by_key(project.key)) == deleted_project

    async def test_when_project_does_not_exist_expect_not_found_exception(self):
        use_case = DeleteProjectUseCaseImpl(InMemoryProjectRepository())
        request = DeleteProjectCommand(
            key=str(uuid4()),
            requested_by="admin@example.com",
            requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        with pytest.raises(EntityNotFoundException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "ENTITY_NOT_FOUND"

    async def test_when_project_already_deleted_expect_already_deleted_exception(self):
        project = _project().delete(
            deleted_at=datetime(2026, 1, 1, tzinfo=UTC), deleted_by="admin@example.com"
        )
        use_case = DeleteProjectUseCaseImpl(InMemoryProjectRepository((project,)))
        request = DeleteProjectCommand(
            key=project.key,
            requested_by="admin@example.com",
            requested_at=datetime(2026, 2, 1, tzinfo=UTC),
        )

        with pytest.raises(ProjectAlreadyDeletedException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "PROJECT_ALREADY_DELETED"
