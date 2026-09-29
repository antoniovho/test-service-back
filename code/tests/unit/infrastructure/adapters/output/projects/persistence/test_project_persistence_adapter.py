from datetime import UTC, datetime

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.projects.project import Project
from test_service.infrastructure.adapters.output.projects.persistence.dtos.project_dto import (
    ProjectDTO,
)
from test_service.infrastructure.adapters.output.projects.persistence.project_persistence_adapter import (  # noqa: E501
    ProjectPersistenceAdapter,
)


def _project() -> Project:
    return Project(
        key="IAG",
        name="AI Gateway",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="admin@example.com",
    )


class _Repository:
    def __init__(self, project: ProjectDTO | None) -> None:
        self.project = project
        self.saved_project: ProjectDTO | None = None

    async def save(self, project: ProjectDTO) -> ProjectDTO:
        self.saved_project = project
        return project

    async def find_by_key(self, key: str) -> ProjectDTO | None:
        return self.project

    async def find_page(self, pagination: PaginationParams) -> Page[ProjectDTO]:
        items = () if self.project is None else (self.project,)
        return Page(items=items, total=len(items))


class TestProjectPersistenceAdapter:
    async def test_when_saving_project_expect_domain_result_and_dto_delegation(self):
        project = _project()
        repository = _Repository(None)
        adapter = ProjectPersistenceAdapter(repository)

        result = await adapter.save(project)

        assert result == project
        assert repository.saved_project is not None
        assert repository.saved_project.key == project.key

    async def test_when_project_exists_expect_mapped_domain_result(self):
        project = _project()
        dto = ProjectDTO(
            key=project.key,
            name=project.name,
            status=project.status.value,
            created_at=project.created_at,
            created_by=project.created_by,
            deleted_at=None,
            deleted_by=None,
        )
        adapter = ProjectPersistenceAdapter(_Repository(dto))

        result = await adapter.find_by_key(project.key)

        assert result == project

    async def test_when_projects_are_paged_expect_mapped_domain_page(self):
        project = _project()
        dto = ProjectDTO(
            key=project.key,
            name=project.name,
            status=project.status.value,
            created_at=project.created_at,
            created_by=project.created_by,
            deleted_at=None,
            deleted_by=None,
        )
        adapter = ProjectPersistenceAdapter(_Repository(dto))

        page = await adapter.find_page(PaginationParams())

        assert page.items == (project,)
        assert page.total == 1
