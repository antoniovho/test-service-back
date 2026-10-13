from uuid import uuid4

import pytest

from test_service.domain.application.services.execution.definition_compiler import (
    DefinitionCompiler,
)
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.exceptions.invalid_definition_exception import (
    InvalidDefinitionException,
)


def _definition(*actions: Action, variables: dict[str, str] | None = None) -> Definition:
    return Definition(variables=variables or {}, actions=actions)


def _http(identifier: str = "request", **configuration: object) -> Action:
    return Action(identifier, "HTTP", {"url": "https://api.test", **configuration})


class TestDefinitionCompiler:
    def test_when_definition_is_valid_expect_actions_compiled_in_order(self) -> None:
        test_case_id = uuid4()
        definition = _definition(_http("first"), Action("second", "SSE", {"url": "https://s.test"}))

        compiled = DefinitionCompiler().compile(test_case_id, definition)

        assert compiled.test_case_id == str(test_case_id)
        assert [(a.identifier, a.action_type, a.position) for a in compiled.actions] == [
            ("first", "HTTP", 0),
            ("second", "SSE", 1),
        ]

    def test_when_no_environment_variables_expect_definition_variables_only(self) -> None:
        definition = _definition(_http(), variables={"tenant": "acme"})

        compiled = DefinitionCompiler().compile(uuid4(), definition)

        assert compiled.variables == {"tenant": "acme"}

    def test_when_environment_variables_are_given_expect_them_to_override_definition(self) -> None:
        definition = _definition(
            _http(), variables={"baseUrl": "https://definition.test", "tenant": "acme"}
        )

        compiled = DefinitionCompiler().compile(
            uuid4(), definition, {"baseUrl": "https://env.test", "apiKey": "key"}
        )

        assert compiled.variables == {
            "baseUrl": "https://env.test",
            "tenant": "acme",
            "apiKey": "key",
        }

    def test_when_compiling_expect_definition_variables_not_modified(self) -> None:
        definition = _definition(_http(), variables={"baseUrl": "https://definition.test"})

        DefinitionCompiler().compile(uuid4(), definition, {"baseUrl": "https://env.test"})

        assert definition.variables == {"baseUrl": "https://definition.test"}

    @pytest.mark.parametrize(
        ("action", "message"),
        [
            (Action("a", "GRPC", {"url": "x"}), "unsupported runner action type 'GRPC'"),
            (Action("a", "HTTP", {}), "must define a non-empty url"),
            (Action("a", "HTTP", {"url": ""}), "must define a non-empty url"),
            (Action("a", "SSE", {"url": 5}), "must define a non-empty url"),
            (Action("a", "HTTP", {"url": "x", "method": ""}), "has an invalid method"),
            (Action("a", "HTTP", {"url": "x", "method": 5}), "has an invalid method"),
        ],
        ids=[
            "unsupported-type",
            "missing-url",
            "empty-url",
            "non-text-url",
            "empty-method",
            "non-text-method",
        ],
    )
    def test_when_action_is_malformed_expect_invalid_definition(self, action, message) -> None:
        definition = _definition(action)

        with pytest.raises(InvalidDefinitionException, match=message) as exc:
            DefinitionCompiler().compile(uuid4(), definition)

        assert exc.value.code == "INVALID_DEFINITION"
