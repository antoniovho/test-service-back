from datetime import UTC, datetime
from uuid import uuid4

import pytest

from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.exceptions.domain_exception import BusinessRuleViolationException
from test_service.domain.model.lifecycle import VersionStatus


def _test_set(**overrides: object) -> TestSet:
    fields = {
        "identifier": uuid4(),
        "project_key": "IAG",
        "set_key": "checkout-regression",
        "version": 1,
        "name": "Checkout regression",
        "items": (uuid4(),),
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": "user@example.com",
    }
    fields.update(overrides)
    return TestSet(**fields)


class TestTestSetInvariants:
    def test_when_version_not_positive_expect_exception(self):
        with pytest.raises(BusinessRuleViolationException) as exc:
            _test_set(version=0)

        assert exc.value.code == "INVALID_TEST_SET"

    def test_when_items_empty_expect_exception(self):
        with pytest.raises(BusinessRuleViolationException) as exc:
            _test_set(items=())

        assert exc.value.code == "INVALID_TEST_SET"

    def test_when_items_duplicated_expect_exception(self):
        item = uuid4()

        with pytest.raises(BusinessRuleViolationException) as exc:
            _test_set(items=(item, item))

        assert exc.value.code == "INVALID_TEST_SET"


class TestTestSetLifecycle:
    def test_when_draft_expect_activate_returns_active(self):
        test_set = _test_set()

        activated = test_set.activate()

        assert activated.status is VersionStatus.ACTIVE

    def test_when_active_expect_deprecate_returns_deprecated(self):
        test_set = _test_set(status=VersionStatus.ACTIVE)

        deprecated = test_set.deprecate()

        assert deprecated.status is VersionStatus.DEPRECATED
