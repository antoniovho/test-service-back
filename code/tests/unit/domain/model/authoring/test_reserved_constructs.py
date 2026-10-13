import pytest

from test_service.domain.commons.reserved_constructs import find_reserved_construct


class TestFindReservedConstruct:
    @pytest.mark.parametrize(
        ("value", "construct"),
        [
            ({"json": {"$ext": {"function": "os:system", "extra_args": ["id"]}}}, "$ext"),
            ({"headers": {"$ext": {"function": "os:getenv"}}}, "$ext"),
            ({"params": {"$ext": {"function": "os:getenv"}}}, "$ext"),
            ({"save": {"$ext": {"function": "os:system"}}}, "$ext"),
            ({"expectedJson": {"data": {"$ext": {"function": "os:system"}}}}, "$ext"),
            ({"json": [{"item": {"$ext": {"function": "os:system"}}}]}, "$ext"),
            ({"json": ({"$ext": {"function": "os:system"}},)}, "$ext"),
            ({"headers": {"X-Leak": "{tavern.env_vars.DATABASE_PASSWORD}"}}, "tavern"),
            ({"url": "https://api.example.test/?k={tavern.env_vars.JIRA_API_TOKEN}"}, "tavern"),
            ({"headers": {"{tavern.env_vars.SECRET}": "value"}}, "tavern"),
            ({"headers": {"X-Leak": "{tavern[env_vars][SECRET]}"}}, "tavern"),
            ({"headers": {"X-Leak": "{tavern.env_vars.SECRET!s}"}}, "tavern"),
            ({"headers": {"X-Leak": "{orderId:{tavern.env_vars.SECRET}}"}}, "tavern"),
            ({"headers": {"X-Leak": "{orderId.__class__}"}}, "__class__"),
            ({"headers": {"X-Leak": "{orderId[__class__]}"}}, "__class__"),
            ("{tavern.env_vars.SECRET}", "tavern"),
        ],
        ids=[
            "ext-in-json",
            "ext-in-headers",
            "ext-in-params",
            "ext-in-save",
            "ext-in-expected-json",
            "ext-in-list",
            "ext-in-tuple",
            "tavern-field-in-header",
            "tavern-field-in-url",
            "tavern-field-in-key",
            "tavern-field-with-index",
            "tavern-field-with-conversion",
            "tavern-field-in-format-spec",
            "dunder-attribute",
            "dunder-index",
            "bare-string",
        ],
    )
    def test_when_value_uses_reserved_construct_expect_description(self, value, construct):
        found = find_reserved_construct(value)

        assert found is not None
        assert construct in found

    @pytest.mark.parametrize(
        "value",
        [
            {"headers": {"X-Order": "{orderId}"}},
            {"url": "{{baseUrl}}/orders/{orderId}"},
            {"headers": {"X-Literal": "{{tavern.env_vars.SECRET}}"}},
            {"json": {"_id": "{_id}", "name": "{items[0].name}"}},
            {"json": {"$ref": "#/definitions/order", "$schema": "draft-07"}},
            {"json": {"text": "unmatched { brace"}},
            {"json": [1, True, None, 2.5]},
            {},
            None,
            42,
        ],
        ids=[
            "tavern-variable",
            "service-and-tavern-variable",
            "escaped-reserved-field",
            "underscore-prefixed-variable",
            "other-dollar-keys",
            "unmatched-brace",
            "non-string-values",
            "empty-mapping",
            "none",
            "number",
        ],
    )
    def test_when_value_has_no_reserved_construct_expect_none(self, value):
        found = find_reserved_construct(value)

        assert found is None

    def test_when_several_constructs_present_expect_first_one_reported(self):
        value = {"json": {"$ext": {"function": "os:system"}}, "headers": {"X": "{tavern.a}"}}

        found = find_reserved_construct(value)

        assert found == "executable directive '$ext'"
