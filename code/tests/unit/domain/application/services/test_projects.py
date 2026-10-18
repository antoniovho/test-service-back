from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from test_service.domain.application.commands.projects import (
    CreateProjectCommand,
    DeleteProjectCommand,
    RestoreProjectCommand,
)
from test_service.domain.application.queries.pagination import Page, PaginationParams
from test_service.domain.application.queries.projects import GetProjectQuery, ListProjectsQuery
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
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
from test_service.domain.application.use_cases.projects.restore_project_use_case import (
    RestoreProjectUseCaseImpl,
)
from test_service.domain.model.exceptions.entity_not_found_exception import (
    EntityNotFoundException,
)
from test_service.domain.model.exceptions.invalid_project_key_exception import (
    InvalidProjectKeyException,
)
from test_service.domain.model.exceptions.project_already_active_exception import (
    ProjectAlreadyActiveException,
)
from test_service.domain.model.exceptions.project_already_deleted_exception import (
    ProjectAlreadyDeletedException,
)
from test_service.domain.model.exceptions.project_already_exists_exception import (
    ProjectAlreadyExistsException,
)
from test_service.domain.model.exceptions.project_restore_required_exception import (
    ProjectRestoreRequiredException,
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

    async def find_page(
        self, pagination: PaginationParams, status: ProjectStatus | None = None
    ) -> Page[Project]:
        projects = tuple(self._projects_by_key.values())
        if status is not None:
            projects = tuple(project for project in projects if project.status is status)
        page_items = projects[pagination.offset : pagination.offset + pagination.limit]
        return Page(items=page_items, total=len(projects))


class AcceptingProjectValidation:
    async def validate(self, project_key: str) -> None:
        return None


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

    async def test_when_status_is_supplied_expect_only_projects_in_that_state(self):
        active = _project()
        deleted = _project(key="DEL").delete(datetime(2026, 1, 2, tzinfo=UTC), "admin@example.com")
        use_case = ListProjectsUseCaseImpl(InMemoryProjectRepository((active, deleted)))

        page = await use_case.execute(
            ListProjectsQuery(pagination=PaginationParams(), status=ProjectStatus.DELETED)
        )

        assert page.items == (deleted,)


class TestCreateProjectUseCaseImpl:
    async def test_when_key_is_unused_expect_project_persisted(self):
        use_case = CreateProjectUseCaseImpl(
            InMemoryProjectRepository(), AcceptingProjectValidation()
        )
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
        use_case = CreateProjectUseCaseImpl(
            InMemoryProjectRepository((existing,)), AcceptingProjectValidation()
        )
        request = CreateProjectCommand(
            key=existing.key,
            name="Another name",
            requested_by="admin@example.com",
            requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        with pytest.raises(ProjectAlreadyExistsException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "PROJECT_ALREADY_EXISTS"

    async def test_when_key_is_deleted_expect_restore_required_exception(self):
        deleted = _project().delete(
            deleted_at=datetime(2026, 1, 2, tzinfo=UTC), deleted_by="admin@example.com"
        )
        use_case = CreateProjectUseCaseImpl(
            InMemoryProjectRepository((deleted,)), AcceptingProjectValidation()
        )
        request = CreateProjectCommand(
            key=deleted.key,
            name="AI Gateway",
            requested_by="admin@example.com",
            requested_at=datetime(2026, 2, 1, tzinfo=UTC),
        )

        with pytest.raises(ProjectRestoreRequiredException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "PROJECT_RESTORE_REQUIRED"
        assert "restore" in exception.value.error_description

    @pytest.mark.parametrize(
        "key",
        ["../myself", "IAG/../../myself", "IAG?expand=lead", "iag"],
        ids=["traversal", "nested-traversal", "query-string", "lowercase"],
    )
    async def test_when_key_is_invalid_expect_exception_before_any_external_call(self, key):
        repository = InMemoryProjectRepository()
        validation = AsyncMock()
        use_case = CreateProjectUseCaseImpl(repository, validation)
        request = CreateProjectCommand(
            key=key,
            name="AI Gateway",
            requested_by="admin@example.com",
            requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        with pytest.raises(InvalidProjectKeyException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "INVALID_PROJECT_KEY"
        validation.validate.assert_not_awaited()
        assert await repository.find_by_key(key) is None


class TestGetProjectUseCaseImpl:
    async def test_when_project_exists_expect_project_returned(self):
        project = _project()
        use_case = GetProjectUseCaseImpl(ProjectResolver(InMemoryProjectRepository((project,))))

        result = await use_case.execute(GetProjectQuery(key=project.key))

        assert result == project

    async def test_when_project_does_not_exist_expect_not_found_exception(self):
        use_case = GetProjectUseCaseImpl(ProjectResolver(InMemoryProjectRepository()))
        request = GetProjectQuery(key="UNKNOWN")

        with pytest.raises(EntityNotFoundException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "ENTITY_NOT_FOUND"


class TestDeleteProjectUseCaseImpl:
    async def test_when_project_exists_expect_project_marked_deleted(self):
        project = _project()
        repository = InMemoryProjectRepository((project,))
        use_case = DeleteProjectUseCaseImpl(repository, ProjectResolver(repository))
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
        repository = InMemoryProjectRepository()
        use_case = DeleteProjectUseCaseImpl(repository, ProjectResolver(repository))
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
        repository = InMemoryProjectRepository((project,))
        use_case = DeleteProjectUseCaseImpl(repository, ProjectResolver(repository))
        request = DeleteProjectCommand(
            key=project.key,
            requested_by="admin@example.com",
            requested_at=datetime(2026, 2, 1, tzinfo=UTC),
        )

        with pytest.raises(ProjectAlreadyDeletedException) as exception:
            await use_case.execute(request)

        assert exception.value.code == "PROJECT_ALREADY_DELETED"


class TestRestoreProjectUseCaseImpl:
    async def test_when_project_is_deleted_and_exists_in_jira_expect_project_restored(self):
        deleted = _project().delete(
            deleted_at=datetime(2026, 1, 2, tzinfo=UTC), deleted_by="admin@example.com"
        )
        repository = InMemoryProjectRepository((deleted,))
        validation = AsyncMock()
        use_case = RestoreProjectUseCaseImpl(repository, ProjectResolver(repository), validation)

        restored = await use_case.execute(
            RestoreProjectCommand(
                key=deleted.key,
                requested_by="admin@example.com",
                requested_at=datetime(2026, 2, 1, tzinfo=UTC),
            )
        )

        assert restored.status is ProjectStatus.ACTIVE
        assert restored.deleted_at is None
        validation.validate.assert_awaited_once_with(deleted.key)
        assert await repository.find_by_key(deleted.key) == restored

    async def test_when_project_is_already_active_expect_conflict_before_jira_validation(self):
        project = _project()
        repository = InMemoryProjectRepository((project,))
        validation = AsyncMock()
        use_case = RestoreProjectUseCaseImpl(repository, ProjectResolver(repository), validation)

        with pytest.raises(ProjectAlreadyActiveException) as exception:
            await use_case.execute(
                RestoreProjectCommand(
                    key=project.key,
                    requested_by="admin@example.com",
                    requested_at=datetime(2026, 2, 1, tzinfo=UTC),
                )
            )

        assert exception.value.code == "PROJECT_ALREADY_ACTIVE"
        validation.validate.assert_not_awaited()
