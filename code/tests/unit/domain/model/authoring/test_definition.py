from types import MappingProxyType

import pytest

from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.exceptions.invalid_action_exception import InvalidActionException
from test_service.domain.model.exceptions.invalid_definition_exception import (
    InvalidDefinitionException,
)


def _action(**overrides: object) -> Action:
    fields = {
        "identifier": "login",
        "action_type": "HTTP_REQUEST",
        "configuration": {"method": "GET"},
    }
    fields.update(overrides)
    return Action(**fields)


class TestAction:
    @pytest.mark.parametrize(
        "field", ["identifier", "action_type", "source"], ids=["identifier", "type", "source"]
    )
    def test_when_text_field_empty_expect_exception(self, field):
        overrides = {field: ""}

        with pytest.raises(InvalidActionException) as exc:
            _action(**overrides)

        assert exc.value.code == "INVALID_ACTION"

    def test_when_configuration_mutated_after_creation_expect_action_unaffected(self):
        configuration = {"method": "GET"}
        action = _action(configuration=configuration)

        configuration["method"] = "POST"

        assert action.configuration["method"] == "GET"

    def test_when_valid_expect_configuration_is_immutable(self):
        action = _action()

        assert isinstance(action.configuration, MappingProxyType)
        with pytest.raises(TypeError):
            action.configuration["method"] = "POST"


class TestDefinition:
    def test_when_schema_version_unsupported_expect_exception(self):
        action = _action()

        with pytest.raises(InvalidDefinitionException) as exc:
            Definition(variables={}, actions=(action,), schema_version="2.0")

        assert exc.value.code == "INVALID_DEFINITION"

    def test_when_no_actions_expect_exception(self):
        with pytest.raises(InvalidDefinitionException) as exc:
            Definition(variables={}, actions=())

        assert exc.value.code == "INVALID_DEFINITION"

    def test_when_duplicate_action_identifiers_expect_exception(self):
        action = _action()

        with pytest.raises(InvalidDefinitionException) as exc:
            Definition(variables={}, actions=(action, action))

        assert exc.value.code == "INVALID_DEFINITION"

    def test_when_empty_variable_name_expect_exception(self):
        action = _action()

        with pytest.raises(InvalidDefinitionException) as exc:
            Definition(variables={"": "value"}, actions=(action,))

        assert exc.value.code == "INVALID_DEFINITION"

    def test_when_variables_mutated_after_creation_expect_definition_unaffected(self):
        variables = {"baseUrl": "https://api.example.com"}
        definition = Definition(variables=variables, actions=(_action(),))

        variables["baseUrl"] = "https://changed.example.com"

        assert definition.variables["baseUrl"] == "https://api.example.com"
