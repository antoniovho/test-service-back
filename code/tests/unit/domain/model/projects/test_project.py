from datetime import UTC, datetime

import pytest

from test_service.domain.model.exceptions.domain_exception import BusinessRuleViolationException
from test_service.domain.model.projects.project import Project, ProjectStatus


def _project(**overrides: object) -> Project:
    fields = {
        "key": "IAG",
        "name": "AI Gateway",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": "admin@example.com",
    }
    fields.update(overrides)
    return Project(**fields)


class TestProjectInvariants:
    def test_when_deleted_without_metadata_expect_exception(self):
        with pytest.raises(BusinessRuleViolationException) as exc:
            _project(status=ProjectStatus.DELETED)

        assert exc.value.code == "INVALID_PROJECT_DELETION"

    def test_when_active_with_deletion_metadata_expect_exception(self):
        with pytest.raises(BusinessRuleViolationException) as exc:
            _project(deleted_at=datetime(2026, 1, 2, tzinfo=UTC), deleted_by="admin@example.com")

        assert exc.value.code == "INVALID_PROJECT_DELETION"


class TestProjectDelete:
    def test_when_active_expect_deleted(self):
        project = _project()
        deleted_at = datetime(2026, 2, 1, tzinfo=UTC)

        deleted = project.delete(deleted_at=deleted_at, deleted_by="admin@example.com")

        assert deleted.status is ProjectStatus.DELETED
        assert deleted.deleted_at == deleted_at
        assert deleted.deleted_by == "admin@example.com"

    def test_when_already_deleted_expect_exception(self):
        project = _project(
            status=ProjectStatus.DELETED,
            deleted_at=datetime(2026, 2, 1, tzinfo=UTC),
            deleted_by="admin@example.com",
        )

        with pytest.raises(BusinessRuleViolationException) as exc:
            project.delete(
                deleted_at=datetime(2026, 2, 2, tzinfo=UTC), deleted_by="admin@example.com"
            )

        assert exc.value.code == "PROJECT_ALREADY_DELETED"
