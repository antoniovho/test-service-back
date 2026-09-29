from datetime import UTC, datetime

from test_service.domain.model.projects.project import Project, ProjectStatus
from test_service.infrastructure.adapters.output.projects.persistence.dtos.project_dto import (
    ProjectDTO,
)
from test_service.infrastructure.adapters.output.projects.persistence.mappers.project_persistence_mapper import (  # noqa: E501
    ProjectPersistenceMapper,
)


class TestProjectPersistenceMapper:
    def test_when_project_is_active_expect_dto_round_trip(self):
        project = Project(
            key="IAG",
            name="AI Gateway",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="admin@example.com",
        )

        restored_project = ProjectPersistenceMapper.to_domain(
            ProjectPersistenceMapper.to_dto(project)
        )

        assert restored_project == project

    def test_when_project_is_deleted_expect_deletion_metadata_round_trip(self):
        project = Project(
            key="IAG",
            name="AI Gateway",
            status=ProjectStatus.DELETED,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="creator@example.com",
            deleted_at=datetime(2026, 2, 1, tzinfo=UTC),
            deleted_by="deleter@example.com",
        )

        dto = ProjectPersistenceMapper.to_dto(project)

        assert dto.status == "DELETED"
        assert ProjectPersistenceMapper.to_domain(dto) == project

    def test_when_dto_is_active_expect_domain_status(self):
        dto = ProjectDTO(
            key="IAG",
            name="AI Gateway",
            status="ACTIVE",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="admin@example.com",
            deleted_at=None,
            deleted_by=None,
        )

        project = ProjectPersistenceMapper.to_domain(dto)

        assert project.status is ProjectStatus.ACTIVE
