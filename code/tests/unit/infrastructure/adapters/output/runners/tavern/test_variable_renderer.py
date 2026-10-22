from types import MappingProxyType

import pytest

from test_service.infrastructure.adapters.output.runners.tavern.variable_renderer import (
    escape_tavern_literal_braces,
    render_service_variables,
)


class TestRenderServiceVariables:
    def test_when_rendering_expect_service_variables_resolved_and_tavern_placeholders_preserved(
        self,
    ) -> None:
        value = {"urls": ["{{baseUrl}}/events/{eventId}"], "enabled": True}

        rendered = render_service_variables(value, {"baseUrl": "https://api.example.test"})

        assert rendered == {
            "urls": ["https://api.example.test/events/{eventId}"],
            "enabled": True,
        }

    def test_when_mapping_is_immutable_expect_rendered_plain_dict(self) -> None:
        value = MappingProxyType({"url": "{{baseUrl}}/orders", "headers": {"X-Tenant": "{{t}}"}})

        rendered = render_service_variables(value, {"baseUrl": "https://api.test", "t": "acme"})

        assert rendered == {"url": "https://api.test/orders", "headers": {"X-Tenant": "acme"}}
        assert type(rendered) is dict

    def test_when_sequence_is_tuple_expect_rendered_list(self) -> None:
        rendered = render_service_variables(("{{a}}", ("{{a}}",)), {"a": "x"})

        assert rendered == ["x", ["x"]]

    def test_when_variable_is_undefined_expect_placeholder_preserved(self) -> None:
        rendered = render_service_variables("{{missing}}", {"other": "x"})

        assert rendered == "{{missing}}"

    @pytest.mark.parametrize(
        ("variable", "expected"),
        [
            ("{tavern.env_vars.SECRET}", "{{tavern.env_vars.SECRET}}"),
            ("a{b}c", "a{{b}}c"),
            ("}{", "}}{{"),
            ("plain", "plain"),
        ],
        ids=["tavern-placeholder", "embedded-braces", "reversed-braces", "no-braces"],
    )
    def test_when_escaping_braces_expect_substituted_value_made_literal(
        self, variable, expected
    ) -> None:
        rendered = render_service_variables("{{value}}", {"value": variable}, escape_braces=True)

        assert rendered == expected

    def test_when_not_escaping_braces_expect_substituted_value_unchanged(self) -> None:
        rendered = render_service_variables("{{value}}", {"value": "a{b}c"})

        assert rendered == "a{b}c"

    def test_when_escaping_braces_expect_literal_text_outside_variables_unchanged(self) -> None:
        rendered = render_service_variables(
            "{orderId}/{{value}}", {"value": "{x}"}, escape_braces=True
        )

        assert rendered == "{orderId}/{{x}}"


class TestEscapeTavernLiteralBraces:
    def test_when_value_contains_regex_quantifier_expect_braces_escaped(self) -> None:
        assert escape_tavern_literal_braces(r"^(?:- [^\r\n]+\n){2}- [^\r\n]+$") == (
            r"^(?:- [^\r\n]+\n){{2}}- [^\r\n]+$"
        )

    def test_when_value_contains_json_example_expect_braces_escaped(self) -> None:
        assert escape_tavern_literal_braces('{"name": string, "age": integer}') == (
            '{{"name": string, "age": integer}}'
        )

    def test_when_value_contains_saved_variable_expect_placeholder_preserved(self) -> None:
        assert escape_tavern_literal_braces("/v1/responses/{response_id}") == (
            "/v1/responses/{response_id}"
        )

    def test_when_value_contains_already_escaped_braces_expect_unchanged(self) -> None:
        assert escape_tavern_literal_braces("{{literal}}") == "{{literal}}"
