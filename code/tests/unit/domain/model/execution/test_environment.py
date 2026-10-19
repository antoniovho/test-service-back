from datetime import UTC, datetime
from uuid import uuid4

import pytest

from test_service.domain.model.exceptions.environment_already_active_exception import (
    EnvironmentAlreadyActiveException,
)
from test_service.domain.model.exceptions.environment_already_inactive_exception import (
    EnvironmentAlreadyInactiveException,
)
from test_service.domain.model.exceptions.invalid_environment_transition_exception import (
    InvalidEnvironmentTransitionException,
)
from test_service.domain.model.exceptions.invalid_secret_reference_exception import (
    InvalidSecretReferenceException,
)
from test_service.domain.model.exceptions.resolved_secret_not_allowed_exception import (
    ResolvedSecretNotAllowedException,
)
from test_service.domain.model.execution.environment import (
    Environment,
    EnvironmentStatus,
    SecretReference,
)


def _environment(**overrides: object) -> Environment:
    fields = {
        "identifier": uuid4(),
        "environment_key": "staging-eu",
        "name": "Staging Europe",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": "user@example.com",
    }
    fields.update(overrides)
    return Environment(**fields)


class TestSecretReference:
    @pytest.mark.parametrize(
        "provider, reference_key", [("", "db-password"), ("vault", "")], ids=["provider", "key"]
    )
    def test_when_field_empty_expect_exception(self, provider, reference_key):
        with pytest.raises(InvalidSecretReferenceException) as exc:
            SecretReference(provider=provider, reference_key=reference_key)

        assert exc.value.code == "INVALID_SECRET_REFERENCE"


class TestEnvironmentSecretsPolicy:
    @pytest.mark.parametrize(
        "key", ["password", "dbPassword", "apiKey", "token", "credential"], ids=lambda key: key
    )
    def test_when_secret_like_key_holds_raw_value_expect_exception(self, key):
        with pytest.raises(ResolvedSecretNotAllowedException) as exc:
            _environment(configuration={key: "raw-value"})

        assert exc.value.code == "RESOLVED_SECRET_NOT_ALLOWED"

    def test_when_secret_like_key_holds_reference_expect_instance(self):
        reference = SecretReference(provider="vault", reference_key="staging/db-password")

        environment = _environment(configuration={"dbPassword": reference})

        assert environment.configuration["dbPassword"] is reference

    def test_when_configuration_mutated_after_creation_expect_environment_unaffected(self):
        configuration = {"region": "eu-west-1"}
        environment = _environment(configuration=configuration)

        configuration["region"] = "eu-west-2"

        assert environment.configuration["region"] == "eu-west-1"


class TestEnvironmentLifecycle:
    def test_when_active_expect_activate_raises_conflict_exception(self):
        environment = _environment(status=EnvironmentStatus.ACTIVE)

        with pytest.raises(EnvironmentAlreadyActiveException) as exc:
            environment.activate()

        assert exc.value.code == "ENVIRONMENT_ALREADY_ACTIVE"

    def test_when_active_expect_deactivate_returns_inactive(self):
        environment = _environment(status=EnvironmentStatus.ACTIVE)

        deactivated = environment.deactivate()

        assert deactivated.status is EnvironmentStatus.INACTIVE

    def test_when_inactive_expect_activate_returns_active(self):
        environment = _environment(status=EnvironmentStatus.INACTIVE)

        activated = environment.activate()

        assert activated.status is EnvironmentStatus.ACTIVE

    def test_when_inactive_expect_deactivate_raises_conflict_exception(self):
        environment = _environment(status=EnvironmentStatus.INACTIVE)

        with pytest.raises(EnvironmentAlreadyInactiveException) as exc:
            environment.deactivate()

        assert exc.value.code == "ENVIRONMENT_ALREADY_INACTIVE"

    @pytest.mark.parametrize("method", ["activate", "deactivate"])
    def test_when_deprecated_expect_transition_raises_exception(self, method):
        environment = _environment(status=EnvironmentStatus.DEPRECATED)
        transition = getattr(environment, method)

        with pytest.raises(InvalidEnvironmentTransitionException) as exc:
            transition()

        assert exc.value.code == "INVALID_ENVIRONMENT_TRANSITION"
