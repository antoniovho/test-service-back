from datetime import UTC, datetime
from uuid import uuid4

import pytest

from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.exceptions.invalid_lifecycle_transition_exception import (
    InvalidLifecycleTransitionException,
)
from test_service.domain.model.exceptions.invalid_precondition_exception import (
    InvalidPreconditionException,
)
from test_service.domain.model.lifecycle import VersionStatus


def _definition() -> Definition:
    return Definition(
        variables={},
        actions=(Action(identifier="check", action_type="ASSERTION", configuration={}),),
    )


def _precondition(**overrides: object) -> Precondition:
    fields = {
        "identifier": uuid4(),
        "project_key": "IAG",
        "precondition_key": "customer-is-authenticated",
        "version": 1,
        "name": "Customer is authenticated",
        "description": "Checks that the customer session is valid",
        "validation_definition": _definition(),
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": "user@example.com",
    }
    fields.update(overrides)
    return Precondition(**fields)


class TestPreconditionInvariants:
    @pytest.mark.parametrize("version", [0, -1], ids=["zero", "negative"])
    def test_when_version_not_positive_expect_exception(self, version):
        with pytest.raises(InvalidPreconditionException) as exc:
            _precondition(version=version)

        assert exc.value.code == "INVALID_PRECONDITION"

    def test_when_metadata_mutated_after_creation_expect_precondition_unaffected(self):
        metadata = {"team": "payments"}
        precondition = _precondition(metadata=metadata)

        metadata["team"] = "checkout"

        assert precondition.metadata["team"] == "payments"


class TestPreconditionLifecycle:
    def test_when_draft_expect_activate_returns_active(self):
        precondition = _precondition()

        activated = precondition.activate()

        assert activated.status is VersionStatus.ACTIVE

    def test_when_active_expect_deprecate_returns_deprecated(self):
        precondition = _precondition(status=VersionStatus.ACTIVE)

        deprecated = precondition.deprecate()

        assert deprecated.status is VersionStatus.DEPRECATED

    def test_when_draft_expect_deprecate_raises_exception(self):
        precondition = _precondition()

        with pytest.raises(InvalidLifecycleTransitionException):
            precondition.deprecate()
