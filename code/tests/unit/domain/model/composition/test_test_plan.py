from datetime import UTC, datetime
from uuid import uuid4

import pytest

from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.exceptions.invalid_test_plan_exception import (
    InvalidTestPlanException,
)
from test_service.domain.model.lifecycle import VersionStatus


def _test_plan(**overrides: object) -> TestPlan:
    fields = {
        "identifier": uuid4(),
        "project_key": "IAG",
        "plan_key": "checkout-nightly",
        "version": 1,
        "name": "Checkout nightly",
        "execution_mode": ExecutionMode.SEQUENTIAL,
        "timeout_seconds": 900,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": "user@example.com",
    }
    fields.update(overrides)
    return TestPlan(**fields)


class TestTestPlanInvariants:
    def test_when_version_not_positive_expect_exception(self):
        with pytest.raises(InvalidTestPlanException) as exc:
            _test_plan(version=0)

        assert exc.value.code == "INVALID_TEST_PLAN"

    def test_when_duplicate_references_within_collection_expect_exception(self):
        test_case_id = uuid4()

        with pytest.raises(InvalidTestPlanException) as exc:
            _test_plan(test_case_ids=(test_case_id, test_case_id))

        assert exc.value.code == "INVALID_TEST_PLAN"

    def test_when_test_case_both_included_and_excluded_expect_exception(self):
        test_case_id = uuid4()

        with pytest.raises(InvalidTestPlanException) as exc:
            _test_plan(test_case_ids=(test_case_id,), exclusions=(test_case_id,))

        assert exc.value.code == "INVALID_TEST_PLAN"


class TestTestPlanLifecycle:
    def test_when_draft_expect_activate_returns_active(self):
        test_plan = _test_plan()

        activated = test_plan.activate()

        assert activated.status is VersionStatus.ACTIVE

    def test_when_active_expect_deprecate_returns_deprecated(self):
        test_plan = _test_plan(status=VersionStatus.ACTIVE)

        deprecated = test_plan.deprecate()

        assert deprecated.status is VersionStatus.DEPRECATED
