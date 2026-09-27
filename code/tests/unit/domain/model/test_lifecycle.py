import pytest

from test_service.domain.model.exceptions.domain_exception import BusinessRuleViolationException
from test_service.domain.model.lifecycle import VersionStatus, activate_status, deprecate_status


class TestActivateStatus:
    def test_when_draft_expect_active(self):
        result = activate_status(VersionStatus.DRAFT)

        assert result is VersionStatus.ACTIVE

    @pytest.mark.parametrize(
        "status", [VersionStatus.ACTIVE, VersionStatus.DEPRECATED], ids=["active", "deprecated"]
    )
    def test_when_not_draft_expect_exception(self, status):
        with pytest.raises(BusinessRuleViolationException) as exc:
            activate_status(status)

        assert exc.value.code == "INVALID_LIFECYCLE_TRANSITION"


class TestDeprecateStatus:
    def test_when_active_expect_deprecated(self):
        result = deprecate_status(VersionStatus.ACTIVE)

        assert result is VersionStatus.DEPRECATED

    @pytest.mark.parametrize(
        "status", [VersionStatus.DRAFT, VersionStatus.DEPRECATED], ids=["draft", "deprecated"]
    )
    def test_when_not_active_expect_exception(self, status):
        with pytest.raises(BusinessRuleViolationException) as exc:
            deprecate_status(status)

        assert exc.value.code == "INVALID_LIFECYCLE_TRANSITION"
