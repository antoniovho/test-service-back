"""Mapping between Projects domain objects and SQLAlchemy DTOs."""

from test_service.domain.model.projects.project import Project, ProjectStatus
from test_service.infrastructure.adapters.output.projects.persistence.dtos.project_dto import (
    ProjectDTO,
)


class ProjectPersistenceMapper:
    """Translate Projects data at the domain and persistence boundary."""

    @staticmethod
    def to_dto(project: Project) -> ProjectDTO:
        """Create a persistence DTO from a Project aggregate."""
        return ProjectDTO(
            key=project.key,
            name=project.name,
            status=project.status.value,
            created_at=project.created_at,
            created_by=project.created_by,
            deleted_at=project.deleted_at,
            deleted_by=project.deleted_by,
        )

    @staticmethod
    def to_domain(project: ProjectDTO) -> Project:
        """Create a Project aggregate from a persistence DTO."""
        return Project(
            key=project.key,
            name=project.name,
            status=ProjectStatus(project.status),
            created_at=project.created_at,
            created_by=project.created_by,
            deleted_at=project.deleted_at,
            deleted_by=project.deleted_by,
        )
