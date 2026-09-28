from datetime import UTC, datetime
from uuid import uuid4

import pytest

from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import (
    PreconditionReference,
    Priority,
    TestCase,
    TestLevel,
    TestType,
)
from test_service.domain.model.exceptions.invalid_lifecycle_transition_exception import (
    InvalidLifecycleTransitionException,
)
from test_service.domain.model.exceptions.invalid_test_case_exception import (
    InvalidTestCaseException,
)
from test_service.domain.model.lifecycle import VersionStatus


def _definition() -> Definition:
    return Definition(
        variables={},
        actions=(Action(identifier="login", action_type="HTTP_REQUEST", configuration={}),),
    )


def _test_case(**overrides: object) -> TestCase:
    fields = {
        "identifier": uuid4(),
        "project_key": "IAG",
        "test_key": "checkout-happy-path",
        "version": 1,
        "name": "Checkout happy path",
        "summary": "Customer completes checkout",
        "objective": "Verify order creation",
        "test_type": TestType.AUTOMATED,
        "test_level": TestLevel.FUNCTIONAL,
        "priority": Priority.HIGH,
        "definition": _definition(),
        "timeout_seconds": 60,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": "user@example.com",
    }
    fields.update(overrides)
    return TestCase(**fields)


class TestTestCaseInvariants:
    @pytest.mark.parametrize("version", [0, -1], ids=["zero", "negative"])
    def test_when_version_not_positive_expect_exception(self, version):
        with pytest.raises(InvalidTestCaseException) as exc:
            _test_case(version=version)

        assert exc.value.code == "INVALID_TEST_CASE"

    def test_when_timeout_not_positive_expect_exception(self):
        with pytest.raises(InvalidTestCaseException) as exc:
            _test_case(timeout_seconds=0)

        assert exc.value.code == "INVALID_TEST_CASE"

    def test_when_duplicate_precondition_references_expect_exception(self):
        reference = PreconditionReference(identifier=uuid4(), precondition_key="auth", version=1)

        with pytest.raises(InvalidTestCaseException) as exc:
            _test_case(preconditions=(reference, reference))

        assert exc.value.code == "INVALID_TEST_CASE"

    def test_when_metadata_mutated_after_creation_expect_test_case_unaffected(self):
        metadata = {"team": "payments"}
        test_case = _test_case(metadata=metadata)

        metadata["team"] = "checkout"

        assert test_case.metadata["team"] == "payments"


class TestTestCaseLifecycle:
    def test_when_draft_expect_activate_returns_active(self):
        test_case = _test_case()

        activated = test_case.activate()

        assert activated.status is VersionStatus.ACTIVE

    def test_when_active_expect_deprecate_returns_deprecated(self):
        test_case = _test_case(status=VersionStatus.ACTIVE)

        deprecated = test_case.deprecate()

        assert deprecated.status is VersionStatus.DEPRECATED

    def test_when_active_expect_activate_raises_exception(self):
        test_case = _test_case(status=VersionStatus.ACTIVE)

        with pytest.raises(InvalidLifecycleTransitionException):
            test_case.activate()
