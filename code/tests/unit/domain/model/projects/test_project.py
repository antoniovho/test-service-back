from datetime import UTC, datetime

import pytest

from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin
from test_service.domain.model.exceptions.invalid_project_deletion_exception import (
    InvalidProjectDeletionException,
)
from test_service.domain.model.exceptions.invalid_project_key_exception import (
    InvalidProjectKeyException,
)
from test_service.domain.model.exceptions.project_already_deleted_exception import (
    ProjectAlreadyDeletedException,
)
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


class TestProjectKey:
    @pytest.mark.parametrize(
        "key",
        [
            "../myself",
            "IAG/../../myself",
            "IAG?expand=lead",
            "IAG#fragment",
            "IAG\n",
            " IAG",
            "IAG ",
            "iag",
            "Iag",
            "I",
            "",
            "1AB",
            "_AB",
            "IAG-1",
            "IAG.1",
            "IAG%2F",
            "IÁG",
            "A" * 21,
        ],
        ids=[
            "parent-traversal",
            "nested-traversal",
            "query-string",
            "fragment",
            "trailing-newline",
            "leading-space",
            "trailing-space",
            "lowercase",
            "mixed-case",
            "single-character",
            "empty",
            "leading-digit",
            "leading-underscore",
            "hyphen",
            "dot",
            "percent-encoding",
            "non-ascii",
            "too-long",
        ],
    )
    def test_when_key_is_not_a_valid_project_key_expect_exception(self, key):
        with pytest.raises(InvalidProjectKeyException) as exc:
            _project(key=key)

        assert exc.value.code == "INVALID_PROJECT_KEY"
        assert exc.value.origin is ErrorOrigin.USER

    @pytest.mark.parametrize(
        "key",
        ["IA", "IAG", "SHOP_1", "A1", "A_B_C", "A" + "B" * 19],
        ids=[
            "two-letters",
            "three-letters",
            "underscore-digit",
            "letter-digit",
            "underscores",
            "max",
        ],
    )
    def test_when_key_is_a_valid_project_key_expect_project_created(self, key):
        project = _project(key=key)

        assert project.key == key

    def test_when_key_is_invalid_expect_message_without_the_rejected_value(self):
        with pytest.raises(InvalidProjectKeyException) as exc:
            _project(key="../myself")

        assert "myself" not in exc.value.error_description
        assert "uppercase" in exc.value.error_description

    def test_when_key_is_not_text_expect_exception(self):
        with pytest.raises(InvalidProjectKeyException):
            _project(key=None)


class TestProjectInvariants:
    def test_when_deleted_without_metadata_expect_exception(self):
        project_fields = {
            "key": "IAG",
            "name": "AI Gateway",
            "created_at": datetime(2026, 1, 1, tzinfo=UTC),
            "created_by": "admin@example.com",
            "status": ProjectStatus.DELETED,
        }

        with pytest.raises(InvalidProjectDeletionException) as exc:
            Project(**project_fields)

        assert exc.value.code == "INVALID_PROJECT_DELETION"
        assert exc.value.origin is ErrorOrigin.INTERNAL

    def test_when_active_with_deletion_metadata_expect_exception(self):
        deleted_at = datetime(2026, 1, 2, tzinfo=UTC)
        project_fields = {
            "key": "IAG",
            "name": "AI Gateway",
            "created_at": datetime(2026, 1, 1, tzinfo=UTC),
            "created_by": "admin@example.com",
            "deleted_at": deleted_at,
            "deleted_by": "admin@example.com",
        }

        with pytest.raises(InvalidProjectDeletionException) as exc:
            Project(**project_fields)

        assert exc.value.code == "INVALID_PROJECT_DELETION"
        assert exc.value.origin is ErrorOrigin.INTERNAL


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
        deleted_at = datetime(2026, 2, 2, tzinfo=UTC)
        deleted_by = "admin@example.com"

        with pytest.raises(ProjectAlreadyDeletedException) as exc:
            project.delete(deleted_at=deleted_at, deleted_by=deleted_by)

        assert exc.value.code == "PROJECT_ALREADY_DELETED"
        assert exc.value.origin is ErrorOrigin.USER
